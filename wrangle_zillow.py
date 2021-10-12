import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import itertools, os, env

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans

from IPython.display import Markdown

import py

from acquire import *

def resolve_missing_values(df, p_col = .5, p_row = .70):
    '''Removes missing values based on proportions
    '''
    l, c  = df.shape
    thresh = int(round(p_col*l, 0))
    df = df.dropna(axis=1, thresh=thresh)
    
    thresh = int(round(p_row*c, 0))
    df = df.dropna(axis=1, thresh=thresh)
    
    return df

def summarize(df):
    result = f'''<center><h2>Summary of DataFrame</h2></center>\n\n'''
    result += f'''### Total Missing Values\n'''
    result += f'''> - There are {df.isna().sum().sum()} missing values.\n'''
    
    # Dataframe head to markdown 
    result += f'''### DataFrame Head\n'''
    result += f'{df.head().to_markdown()}\n\n'
    
    # Dataframe info to markdown
    result += '### DataFrame Info\n'
    info = pd.DataFrame({ 'nulls' : df.isna().sum(), 'dtypes' : df.dtypes}).reset_index()\
.rename(columns={'index': 'column_name'})
    result += f'{info.to_markdown()}\n\n'
    
    # Dataframe description to markdown
    description = df.describe().T
    result += '### DataFrame Description\n'
    result += f'{description.to_markdown()}\n\n'
            
    return result

def remove_outliers(df, k, col_list):
    for col in col_list:
        q1, q3 = df[col].quantile([.25, .75])
        iqr = q3 - q1
        upper_bound = q3 + k * iqr
        lower_bound = q1 - k * iqr
        
        df = df[(df[col] > lower_bound) & (df[col] < upper_bound)]
    return df 

def wrangle(df):
    df = remove_outliers(df, 1.5, ['bedroomcnt', 'bathroomcnt', 'taxvaluedollarcnt', 'taxamount', 'lotsizesquarefeet', 'structuretaxvaluedollarcnt'])

    # Handle null values
    for col in df.columns:
        if df[col].dtype != 'object':
            median = df[col].median()
            df[col] = df[col].fillna(median)

    df['county'] = df.fips.apply(
        lambda x: 'Los Angeles' if int(x) == 6037 
        else 'Orange' if int(x) == 6059 
        else 'Ventura')
    
    # Filter outliers for certain featuers

    df = df[(df.taxamount < 4_000_000) & (df.calculatedfinishedsquarefeet < 8_000)]

    return df

def zillow_split(df, target):
    '''This function take in get_zillow  from aquire.py and performs a train, validate, test split
    Returns train, validate, test, X_train, y_train, X_validate, y_validate, X_test, y_test as partitions
    and prints out the shape of train, validate, test.
    '''
    # create train and validate and test datasets
    train_and_validate, test = train_test_split(df, train_size=0.8, random_state=123)
    train, validate = train_test_split(train_and_validate, train_size=0.75, random_state=123)

    # Split into X and y
    X_train = train.drop(columns=[target])
    y_train = train[target]

    X_validate = validate.drop(columns=[target])
    y_validate = validate[target]

    X_test = test.drop(columns=[target])
    y_test = test[target]

    return X_train, X_validate, X_test, y_train, y_validate, y_test

def min_max_scaler(X_train, X_validate, X_test, numeric_cols):
    # create the scaler object and fit it to X_train (i.e. identify min and max)
    scaler = MinMaxScaler(copy=True).fit(X_train[numeric_cols])
    
    # scale 
    X_train_scaled_array = scaler.transform(X_train[numeric_cols])
    X_validate_scaled_array = scaler.transform(X_validate[numeric_cols])
    X_test_scaled_array = scaler.transform(X_test[numeric_cols])

    # convert arrays to dataframes
    X_train_scaled = pd.DataFrame(
        X_train_scaled_array, columns=numeric_cols).set_index([X_train.index.values])
    X_validate_scaled = pd.DataFrame(
        X_validate_scaled_array, columns=numeric_cols).set_index([X_validate.index.values])

    X_test_scaled = pd.DataFrame(
        X_test_scaled_array, columns=numeric_cols).set_index([X_test.index.values])

    for i in numeric_cols:
        X_train[i] = X_train_scaled[i]
        X_validate[i] = X_validate_scaled[i]
        X_test[i] = X_test_scaled[i]

    return X_train, X_validate, X_test


def create_cluster(df, X, k, col_name = None):
    scaler = StandardScaler(copy=True).fit(X)
    X_scaled = pd.DataFrame(scaler.transform(X), columns=X.columns.values).set_index([X.index.values])
    kmeans = KMeans(n_clusters = k, random_state = 123)
    kmeans.fit(X_scaled)
    centroids_scaled = pd.DataFrame(kmeans.cluster_centers_, columns = list(X))

    if col_name == None:
        df[f'clusters_{k}'] = kmeans.predict(X_scaled)
    else:
        df[col_name] = kmeans.predict(X_scaled)

def train_validate_test_split(df):
    train_and_validate, test = train_test_split(df, train_size=0.8, random_state=123)
    train, validate = train_test_split(train_and_validate, train_size=0.75, random_state=123)

    return train, validate, test