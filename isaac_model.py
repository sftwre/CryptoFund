import os
import sys
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from keras.models import Sequential, load_model
from keras.layers import Dense
from keras.layers import LSTM

from sklearn.preprocessing import MinMaxScaler
min_max_scaler = MinMaxScaler()

# directories for model and saved images
imagesDir = "./images/"
modelDir = "./model/"
fname = "lstm.h5"

# make images dir for plots if non exists
if not os.path.exists(imagesDir):
    os.mkdir(imagesDir)

# make dir for model if non exists
if not os.path.exists(modelDir):
    os.mkdir(modelDir)

# read data
df = pd.read_csv("./data/bitcoin_price.csv")

# drop date col
df.drop(["Date"], axis=1, inplace=True)

# replace '-' with np.NaN
df.replace('-', np.NaN, inplace=True)

# drop rows with NaN
df.dropna(axis=0, how="any", inplace=True)

#  transform volume and market cap into floats
df["Volume"] = df["Volume"].str.replace(',', '').astype('float64')
df["Market Cap"] = df["Market Cap"].str.replace(',', '').astype('float64')

# split into training and testing
prediction_days = 30

df_train = df[:len(df)-prediction_days]
df_test = df[len(df)-prediction_days:]

# normalize and split into training and testing
training_set = df_train.values
training_set = min_max_scaler.fit_transform(training_set)

x_train = training_set[0:len(training_set)-1]
y_train = training_set[1:len(training_set)+1]
x_train = x_train.reshape((len(x_train), 1, 6))

num_units = 6
activation_function = 'sigmoid'
optimizer = 'adam'
loss_function = 'mean_squared_error'
batch_size = 5
num_epochs = 100

# load model if it exits
if os.path.exists(modelDir + fname):
    regressor = load_model(modelDir + fname)

else:
    # Initialize the RNN
    regressor = Sequential()

    # Adding the input layer and the LSTM layer
    regressor.add(LSTM(units = num_units, activation = activation_function, input_shape=(1, 6)))

    # Adding the output layer
    regressor.add(Dense(units = 6))

    # Compiling the RNN
    regressor.compile(optimizer = optimizer, loss = loss_function)

    # Using the training set to train the model
    regressor.fit(x_train, y_train, batch_size = batch_size, epochs = num_epochs)

    # save model
    regressor.save(modelDir + fname)

# predict price
test_set = df_test.values

inputs = np.reshape(test_set, (len(test_set), 6))
inputs = min_max_scaler.transform(inputs)
inputs = np.reshape(inputs, (len(inputs), 1, 6))

predicted_price = regressor.predict(inputs)
predicted_price = min_max_scaler.inverse_transform(predicted_price)

# plot results
plt.figure(figsize=(25, 25), dpi=80, facecolor = 'w', edgecolor = 'k')

plt.plot(test_set[:, 0], color='red', label='Real BTC Price')
plt.plot(predicted_price[:, 0], color = 'blue', label = 'Predicted BTC Price')

plt.title('BTC Price Prediction', fontsize = 40)
plt.xlabel('Time', fontsize=40)
plt.ylabel('BTC Price(USD)', fontsize = 40)
plt.legend(loc = 'best')
plt.savefig(imagesDir + "btc_price_prediction.png")