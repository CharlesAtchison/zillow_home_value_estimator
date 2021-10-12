from env import user, password, host
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import pandas as pd
import os


def get_db_url(username: str, hostname: str , password: str, database_name: str):
    '''
    Takes username, hostname, password and database_name and 
    returns a connection string
    '''
    connection = f'mysql+pymysql://{username}:{password}@{hostname}/{database_name}'
    
    return connection


def get_zillow_data():
    filename = "zillow_data.csv"

    if os.path.isfile(filename):
        return pd.read_csv(filename, index_col=[0])

    else:
        conn = get_db_url(username=user, password=password, hostname=host, database_name='zillow')
        
        sql = '''
        SELECT properties_2017.id, properties_2017.bathroomcnt, properties_2017.bedroomcnt, calculatedfinishedsquarefeet, fips, latitude, longitude, lotsizesquarefeet, properties_2017.propertylandusetypeid, rawcensustractandblock,
 regionidcity, regionidcounty, regionidzip, roomcnt, yearbuilt, structuretaxvaluedollarcnt,
 taxvaluedollarcnt, assessmentyear, landtaxvaluedollarcnt, taxamount, logerror, transactiondate, last_trans_date
        FROM properties_2017
        LEFT OUTER JOIN airconditioningtype 
        ON airconditioningtype.airconditioningtypeid = properties_2017.airconditioningtypeid
        LEFT OUTER JOIN architecturalstyletype
        ON architecturalstyletype.architecturalstyletypeid = properties_2017.architecturalstyletypeid
        LEFT OUTER JOIN buildingclasstype 
        ON buildingclasstype.buildingclasstypeid = properties_2017.buildingclasstypeid
        LEFT OUTER JOIN heatingorsystemtype
        ON heatingorsystemtype.heatingorsystemtypeid = properties_2017.heatingorsystemtypeid
        LEFT OUTER JOIN predictions_2017
        ON predictions_2017.id = properties_2017.id
        INNER JOIN (
        SELECT id, MAX(transactiondate) as last_trans_date 
        FROM predictions_2017
        GROUP BY id
        ) predictions ON predictions.id = properties_2017.id AND predictions_2017.transactiondate = predictions.last_trans_date
        LEFT OUTER JOIN propertylandusetype
        ON propertylandusetype.propertylandusetypeid = properties_2017.propertylandusetypeid
        LEFT OUTER JOIN storytype
        ON storytype.storytypeid = properties_2017.storytypeid
        LEFT OUTER JOIN typeconstructiontype
        ON typeconstructiontype.typeconstructiontypeid = properties_2017.typeconstructiontypeid
        JOIN unique_properties
        ON unique_properties.parcelid = properties_2017.parcelid
        WHERE latitude IS NOT NULL and longitude IS NOT NULL
        AND properties_2017.calculatedfinishedsquarefeet > 350 
        AND properties_2017.bathroomcnt > 0
        AND properties_2017.bedroomcnt > 0; 
        '''
        df = pd.read_sql(sql, conn)

        df.to_csv(filename)

        return df

def train_validate_test_split(df, target, seed=123):
    '''
    This function takes in a dataframe, the name of the target variable
    (for stratification purposes), and an integer for a setting a seed
    and splits the data into train, validate and test. 
    Test is 20% of the original dataset, validate is .30*.80= 24% of the 
    original dataset, and train is .70*.80= 56% of the original dataset. 
    The function returns, in this order, train, validate and test dataframes. 
    '''
    train_validate, test = train_test_split(df, test_size=0.2, 
                                            random_state=seed, 
                                            )
    train, validate = train_test_split(train_validate, test_size=0.3, 
                                       random_state=seed,
                                       )
    return train, validate, test


def fetch_data_dict(df, target):
    ''' Fetches and formats a data_dict to put into project README.md
    returns two pandas DataFrame formatted markdown.
    '''
    data_dict = {
        'bedroomcnt':'quantifies the number of bedrooms in a house',
        'bathroomcnt':'quantifies the number of bathrooms in a house',
        'calculatedfinishedsquarefeet':'quantifies the calculated number of sq ft.',
        'taxvaluedollarcnt':'taxable value for the home',
        'yearbuilt':'defines the year that the home was built',
        'taxamount':'quantifies the amount of taxes the home pays',
        'fips'	:'Federal state code',
        'regionidzip': '',
        'regionidcity': '',
        'lotsizesquarefeet': ''}

    feature_dict = pd.DataFrame([{'Feature': col, 
         'Datatype': f'{df[col].count()} non-null: {df[col].dtype}',
        'Definition' : data_dict[col]} for col in df.columns]).set_index('Feature').to_markdown()
    target_dict = pd.DataFrame([{'Target': col, 
         'Datatype': f'{df[col].count()} non-null: {df[col].dtype}',
        'Definition' : data_dict[col]} for col in df.columns if col == target]).set_index('Target').to_markdown()
    return (target_dict, feature_dict)
