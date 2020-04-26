# -*- coding: utf-8 -*-
"""
Created on Fri Apr 24 21:01:56 2020

@author: techm
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

#import ray
#try:
#    from ray.rllib.agents.agent import get_agent_class
#except ImportError:
#    from ray.rllib.agents.registry import get_agent_class
#from ray.tune import run_experiments
#from ray.tune.registry import register_env

def load_extract(cryptocurrency):
    """
    Loads data used for training/trading
    :param cryptocurrency: crypto to trade
    :return: dataframe of data
    """
    df = pd.read_csv(f'features/{cryptocurrency}.csv')
    df = df.drop(columns=['30 mavg', '30 std', '26 ema', '12 ema', 'MACD', 'Signal'], axis=1)
    df = df['Close'].copy()
    df = df[0:10].copy()
    return df


# load data
df_btc = load_extract('bitcoin')
df_eth = load_extract('ethereum')
df_dash = load_extract('dash')
df_ltc = load_extract('litecoin')
df_xmr = load_extract('monero')
df_xrp = load_extract('ripple')

trent_output = pd.DataFrame(data=[df_btc, df_eth, df_dash, df_ltc, df_xmr, df_xrp])
today_price = np.array([df_btc[0], df_eth[0], df_dash[0], df_ltc[0], df_xmr[0], df_xrp[0]])

trent_output.index = ['bitcoin', 'ethereum', 'dash', 'litecoin', 'monero', 'ripple'] 
sns.distplot(df_btc, bins=20, kde=False, rug=True)

trent_output = trent_output.T
isaac_input = pd.DataFrame(columns=trent_output.columns)
isaac_input.loc[0] = np.empty(6)

# predicted price for each coin
for coin in list(trent_output.columns):
    if len(trent_output[coin].mode()) < 10:
        modes = list(trent_output[coin].mode())
        mean = trent_output[coin].mean()
        d = defaultdict(float)
        for mode in modes:
            distance = abs(mode - mean)
            d[mode] = distance
        result = min(d.items(), key=lambda x: x[1])
        isaac_input[coin] = trent_output[coin].mode()[0]
    else:
        isaac_input[coin] = trent_output[coin].median()


# confidence intervals
c_values = np.zeros(6)

coin_names = trent_output.columns.to_list()

gains = np.zeros(6)

weights = np.array([1, 0, 0, 0, 0, 0])

# compute confidence for each coin
for i, coin in enumerate(coin_names):

    # one precent range
    one_high, one_low = 1.01 * isaac_input[coin].values[0], .99 * isaac_input[coin].values[0]

    # ten percent range
    ten_high, ten_low = 1.10 * isaac_input[coin].values[0], .90 * isaac_input[coin].values[0]

    obs = trent_output[coin].values

    # find observations within one percent and ten percent of the predicted price
    num  = np.count_nonzero(np.logical_and(obs >= one_low, obs <= one_high))
    den = np.count_nonzero(np.logical_and(obs >= ten_low, obs <= ten_high))

    c_values[i] = num / den


# compute percent increase
gains[0] = (isaac_input["bitcoin"].values[0] / df_btc.iloc[0]) - 1
gains[1] = (isaac_input["ethereum"].values[0] / df_eth.iloc[0]) - 1
gains[2] = (isaac_input["dash"].values[0] / df_dash.iloc[0]) - 1
gains[3] = (isaac_input["litecoin"].values[0] / df_ltc.iloc[0]) - 1
gains[4] = (isaac_input["monero"].values[0] / df_xmr.iloc[0]) - 1
gains[5] = (isaac_input["ripple"].values[0] / df_xrp.iloc[0]) - 1

isaac_input = isaac_input.T
isaac_input = isaac_input.rename(columns={0: "Pred_Price"})
isaac_input['CurrentPrice'] = today_price
isaac_input['Gain'] = gains
isaac_input['Weights'] = weights
isaac_input["C_value"] = c_values


max_gain = isaac_input.index[isaac_input['Gain'] == isaac_input['Gain'].max()].to_list()[0]

losses = sorted(isaac_input["Gain"].to_list())

# trade from currency with least gain to currency with most gain

for loss in losses:

    index = isaac_input.index[isaac_input['Gain'] == loss].to_list()

    if isaac_input.at[index[0], "Weights"] != 0 and isaac_input.loc[index[0], "Gain"] < 0 :
        min_gain = index[0]
        break

allocate = isaac_input.loc[min_gain, "Weights"] * isaac_input.loc[min_gain, "C_value"]

update = (1 - isaac_input.loc[min_gain, "C_value"]) * isaac_input.loc[min_gain, "Weights"]

isaac_input.loc[min_gain, "Weights"] = update

new_currency = (allocate / isaac_input.loc[max_gain, "CurrentPrice"]) * isaac_input.loc[min_gain , "CurrentPrice"]

isaac_input.loc[max_gain, "Weights"] = new_currency

fund_value = isaac_input["Weights"] * isaac_input["Pred_Price"]
fund_value = fund_value.sum()