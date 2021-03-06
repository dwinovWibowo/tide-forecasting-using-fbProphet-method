# -*- coding: utf-8 -*-
"""sea_level forecasting with  prophet_experiment (2).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/17zo3S-FPJ2Ce5LAeVFm9BQE4HFaNuOaL

#di karenakan kita akan menggunakan plotly  dan plotly belum include dalam paket  jadi pertama kita akan menginstal plotly
"""

pip install plotly_express

"""#lakukan import library yang akan di **gunakan**"""

import pandas as pd
import numpy as np
from pandas import datetime
import random
import matplotlib.pyplot as plt 
import plotly_express as px
from sklearn.metrics import mean_squared_error
from fbprophet import Prophet

"""# melakukan load data set yang akan digunakan"""

df=pd.read_excel('/content/drive/MyDrive/Colab Notebooks/Data_SL_Cilacap_01012019_25112019.xlsx', header=1)
df.shape#mengecek bentuk dimensi dari data set

df.head()#melakukan cek 5 data teratas dari data set

"""#berdasarkan show 5 data teratas menunjukan data permenit dan karena data yang akan digunakan dalam studi kasus ini merupakan data perjam makan akan dilakukan resampling"""

df1=df.iloc[:,[0,3]] #mengambil bagian feature yang akan digunakan saja
#karena nama kolom ds dan y di putuhkan dalam menggunakan prophet maka kita akan menganti nama kolom pada data frame
df1 = df1.rename(columns = {"Time (UTC)":"ds","prs(m)":"y"})

df1.head()

df1=df1.resample(rule='h', on='ds').median()# meresample data menjadi data perjam menggunakan metode median
df1.head()

df1.isnull().sum()# melakukan pengecekan apakah ada nilai nul yang terdapat dalam data set

df1['y'].interpolate(method='spline',order=3,inplace= True)# kita melakukan interpolate untuk mengisi nilai miss values dengan melakukan interpolasi dengan metode spline orde 3

df1.head()

"""# melakukan visualisasi dari data set akan digunakan"""

df1['ds']=df1.index
df1.shape

fig = fig = px.line(df1, x='ds', y='y')
fig.show()

"""#melakukan decompose untuk melihat bentuk trend  dan seasonality dari data """

ddaily=df.iloc[:1440,[0,3]]
ddaily= ddaily.rename(columns = {"Time (UTC)":"ds","prs(m)":"y"})
dweekly=df1.iloc[:168,:]#mengambil data selama jangka waktu 1 minggu dari data set
dsmestr=df1.iloc[:4248,:]#mengambil data selama jangka waktu 1 semester dari data set
dqwrter=df1.iloc[:2832,:]#mengambil data selama jangka waktu 1 quarter dari data set
dmonthly=df1.iloc[:708,:]#mengambil data selama jangka waktu 1 bulan dari data set

from statsmodels.tsa.seasonal import seasonal_decompose
result = seasonal_decompose(df1['y'], model='additive')#melakukan decompose seluruh data set
result.plot()

result = seasonal_decompose(dweekly['y'], model='additive')#melakukan decompose data 1 minggu 
result.plot()

result = seasonal_decompose(dmonthly['y'], model='additive')#melakukan decompose data 1 bulan
result.plot()

result = seasonal_decompose(dsmestr['y'], model='additive')#melakukan decompose data 1 semester
result.plot()

result = seasonal_decompose(dqwrter['y'], model='additive')#melakukan decompose data 1 quarter
result.plot()

"""# membagi data menjadi test dan train"""

#dalam kasus ini sy akan mengunakan setengah dri data untuk menjadi train 
d_test=df1.iloc[7560:,:]
d_train=df1.iloc[3648:7559,:]

print(d_test.shape)
print(d_train.shape)

fig = fig = px.line(d_test, x='ds', y='y')#memvisualisasi data yang digunakan sebagai data test
fig.show()

fig = fig = px.line(d_train, x='ds', y='y')#memvisualisasi data yang digunakan sebagai data train
fig.show()

"""#membuat model prophet tanpa melalukan tune pada seasonality parameter"""

m = Prophet( interval_width=0.95,) # the Prophet class (model)

m.fit(d_train) # fit the model using all data

future = m.make_future_dataframe(periods=(1336),freq='H',) #we need to specify the number of days in future
prediction = m.predict(future)

m.plot(prediction)# seperti yang dapat dilihat confident dari model berusaha melakukan fit tetapi model belum dapat mengikuti seasonality dr data set

import statsmodels.api as sm
sm.graphics.tsa.plot_acf(d_train['y'].values.squeeze(),lags=162)
plt.ylim(-1,1)
plt.xlim(72,75)
plt.show()

"""# membuat model dengan melakukan  tune pada parameter modelnya
parameter yang akan sangat berdampak adalah parameter seasonality disini seperti berdasarkan yang kita lihat dari preproses untuk melihat tren dan seasonality dari dataset dataset memiliki seasonality selama 2 hari sekali, 1 bulan sekali dan 2 bulan sekali hal itu juga di tunjukan berdasarkan autocorelasion dari datanya
"""

m = Prophet( interval_width=0.95, weekly_seasonality=False,daily_seasonality=False,changepoint_prior_scale=0.07) # the Prophet class (model)
m.add_seasonality(name='daily',period=2,fourier_order=4,prior_scale=20,mode='additive')
m.add_seasonality(name='monthly',period=29.5,fourier_order=100,prior_scale=15,mode='additive')
m.add_seasonality(name='weekly',period=7,fourier_order=20,prior_scale=6,mode='additive')
m.add_seasonality(name='weekly',period=29.5*2.3,fourier_order=100,prior_scale=5,mode='additive')
#perior_scale digunakan untuk menentukan predik lebih fit ke seasonality yang mana
m.fit(d_train) # fit the model using all data

future = m.make_future_dataframe(periods=(1336),freq='H',) #we need to specify the number of days in future
prediction = m.predict(future)

m.plot(prediction)

fig = fig = px.line(prediction.iloc[2912:], x='ds', y='yhat')
fig.show()

prediction.info()

pred=prediction.iloc[3912:4248,[0,21]]
pred['ds']=pd.to_datetime(pred.ds)
pred.info()

"""#memvisualisasikan perbandingan data real dan hasil prediksi serta membuat rmse dan r2 dr model"""

plt.figure(figsize=(16,8))
plt.rc('xtick', labelsize=16) 
plt.rc('ytick', labelsize=14) 
plt.plot(d_test['y'].values, label='Test')
plt.plot(pred['yhat'].values, label='pred')
plt.legend(loc='best')
plt.show()

from sklearn.metrics import r2_score
r2=r2_score(d_test['y'],  pred['yhat'])
rms1 = np.sqrt(mean_squared_error(d_test['y'], pred['yhat']))
print(r2," , ",rms1)

"""**note:** selain mentune seasonality kita jg dapat mentune change_point perior scale dr model untuk menyesuaikan apakah hasil prediksi/ model akan mengikuti data set 
---

**note:** hati" saat melakukan tune agas model yang dibuat tidak overfit
untuk memahami definisi lebih lanjut dari parameter prophet bisa melihat langsung pada definisi di prophet dengan mengetik kan code" prophet??"


---


"""