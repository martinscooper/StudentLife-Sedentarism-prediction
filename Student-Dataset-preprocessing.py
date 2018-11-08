'''
# createSensingTable('dataset/sensing/activity/activity_u').to_csv('processing/activity.csv', index=False)
# createSensingTable('dataset/sensing/audio/audio_u').to_csv('processing/audio.csv', index=False)
# createSensingTable('dataset/sensing//_u').to_csv('processing/.csv', index=False)
# createSensingTable('dataset/sensing/dark/dark_u').to_csv('processing/dark.csv', index=False)
# createSensingTable('dataset/sensing/gps/gps_u').to_csv('processing/gps.csv', index=False)
# createSensingTable('dataset/sensing/phonelock/phonelock_u').to_csv('processing/phonelock.csv', index=False)
# createSensingTable('dataset/sensing/wifi/wifi_u').to_csv('processing/wifi.csv', index=False)
# createSensingTable('dataset/sensing/phonecharge/phonecharge_u').to_csv('processing/phonecharge.csv', index=False)
# createSensingTable('dataset/calendar/calendar_u').to_csv('processing/calendar.csv', index=False)
#createSensingTable('dataset/sensing/wifi_location/wifi_location_u').to_csv('processing/wifi_location.csv', index=False)


#Audio Inference
#ID	Description
#0	Silence
#1	Voice
#2	Noise
#3	Unknown

#Activity Inference ID	Description
#0	Stationary
#1  Walking
#2	Running
#3	Unknown

cuando la actividad que mas se lleva a cabo es unknown, el porcentaje de actividad
sedentaria para esa hora es similar al promedio de actividad sedentaria para las
hora donde la act q mas se lleva a cabo es 1 (walking), por eso se lo va a tomar
como si fuera de ese tipo

activitymajor
0    0.937012
1    0.296808
2    0.073199
3    0.201710


#
#
# ## Feature generation ##
#
# **Features:**
# * Stationaty mean per hour
# * Day of the week (weekday,saturday or sunday)
# * Hour of the day
# * activityMajor: the type of activity with the most instances in a 1-hour time bucket
# * audioMajor
# * latitude average and stv
# * longitud avg and stv
# * is Charging

#como tratar los valores nulos??
    # los deadlines son solo de 44 de 49 estudiantes
    # los datos de audio no estan para todas la horas de todos los estudiantes
    # los datos de ubicacion son infimos


hay 14420.575126 en promedio de muestros de actividad por hora
'''
from sklearn.preprocessing import LabelEncoder
from utilfunction import *
from sklearn import cluster
import math

# prepare activity data
sdata = pd.read_csv('processing/activity.csv')
sdata.columns = ['time', 'activityId', 'userId']
sdata = sdata.loc[sdata['activityId'] != 3]
sdata['time'] = pd.to_datetime(sdata['time'], unit='s').dt.floor('h')
sdata['slevel'] = sdata['activityId'] == 0

# sedentary mean
s = pd.DataFrame(sdata.groupby( by= ['userId', pd.Grouper(key='time', freq='H')] )['slevel'].mean())

# hourofday
s['hourofday'] = s.index.get_level_values('time').hour

s['partofday'] = 'night'
s.loc[(s['hourofday'] >= 5) & (s['hourofday'] < 12), 'partofday'] = 'morning'
s.loc[(s['hourofday'] >= 12) & (s['hourofday'] < 17), 'partofday'] = 'afternoon'
s.loc[(s['hourofday'] >= 17) & (s['hourofday'] < 21), 'partofday'] = 'evening'

# dayofweek
#s.loc[s.index.get_level_values('time').dayofweek == 0, 'dayofweek'] = 'saturday'
s['dayofweek'] = 'monday'
s.loc[s.index.get_level_values('time').dayofweek == 1, 'dayofweek'] = 'tuesday'
s.loc[s.index.get_level_values('time').dayofweek == 2, 'dayofweek'] = 'wednesday'
s.loc[s.index.get_level_values('time').dayofweek == 3, 'dayofweek'] = 'thursday'
s.loc[s.index.get_level_values('time').dayofweek == 4, 'dayofweek'] = 'friday'
s.loc[s.index.get_level_values('time').dayofweek == 5, 'dayofweek'] = 'saturday'
s.loc[s.index.get_level_values('time').dayofweek == 6, 'dayofweek'] = 'sunday'

# activitymajor
s['activitymajor'] = sdata.groupby(['userId', 'time'])['activityId'].apply(Most_Common)

s['pastminutes'] = s.index.get_level_values(1).hour * 60 + s.index.get_level_values(1).minute
s['remainingminutes'] = 24*60 - s['pastminutes']

#logs per activity
s.loc[:, 'stationaryCount'] = sdata.loc[sdata['activityId'] == 0, ].groupby(['userId', 'time'])['slevel'].count()
s.loc[s['stationaryCount'].isna(), 'stationaryCount'] = 0

s.loc[:, 'walkingCount'] = sdata.loc[sdata['activityId'] == 1, ].groupby(['userId', 'time'])['slevel'].count()
s.loc[s['walkingCount'].isna(), 'walkingCount'] = 0

s.loc[:, 'runningCount'] = sdata.loc[sdata['activityId'] == 2, ].groupby(['userId', 'time'])['slevel'].count()
s.loc[s['runningCount'].isna(), 'runningCount'] = 0

# prepare audio data
adata = pd.read_csv('processing/audio.csv')
adata.columns = ['time', 'audioId', 'userId']
adata['time'] = pd.to_datetime(adata['time'], unit='s')
adata = adata[adata['audioId'] != 3]
adata['time'] = adata['time'].dt.floor('h')

# audiomajor
# los siguientes usuarios poseen horas completas en las cuales no tienen ningun registro de audio
# s[s['audiomajor'].isna()].groupby('userId')['audiomajor'].count()
s['audiomajor'] = np.NaN
s['audiomajor'] = adata.groupby(['userId', 'time'])['audioId'].apply(Most_Common).astype('int')


#0	Silence
#1	Voice
#2	Noise
#3	Unknow

s.loc[:, 'silenceCount'] = adata.loc[adata['audioId'] == 0, ].groupby(['userId', 'time'])['audioId'].count()
s.loc[s['silenceCount'].isna(), 'silenceCount'] = 0

s.loc[:, 'voiceCount'] = adata.loc[adata['audioId'] == 1, ].groupby(['userId', 'time'])['audioId'].count()
s.loc[s['voiceCount'].isna(), 'voiceCount'] = 0

s.loc[:, 'noiseCount'] = adata.loc[adata['audioId'] == 2, ].groupby(['userId', 'time'])['audioId'].count()
s.loc[s['noiseCount'].isna(), 'noiseCount'] = 0

s.loc[:, 'unknownAudioCount'] = adata.loc[adata['audioId'] == 1, ].groupby(['userId', 'time'])['audioId'].count()
s.loc[s['unknownAudioCount'].isna(), 'unknownAudioCount'] = 0


# latitude and longitude mean and std
gpsdata = pd.read_csv('processing/gps.csv')
gpsdata['time'] = pd.to_datetime(gpsdata['time'], unit='s')
gpsdata['time'] = gpsdata['time'].dt.floor('h')

kmeans = cluster.KMeans(n_clusters=15)
kmeans.fit(gpsdata[['latitude', 'longitude']].values)
gpsdata['place'] = kmeans.predict(gpsdata[['latitude', 'longitude']])
s['latitudeMean'] = gpsdata.groupby(['userId', 'time'])['latitude'].mean()
s['longitudeMean'] = gpsdata.groupby(['userId', 'time'])['longitude'].mean()

s['latitudeMedian'] = gpsdata.groupby(['userId', 'time'])['latitude'].median()
s['longitudeMedian'] = gpsdata.groupby(['userId', 'time'])['longitude'].median()

s['latitudeStd'] = gpsdata.groupby(['userId', 'time'])['latitude'].std()
s['longitudeStd'] = gpsdata.groupby(['userId', 'time'])['longitude'].std()
s['place'] = gpsdata.groupby(['userId', 'time'])['place'].apply(Most_Common)
s['distanceTraveld'] = gpsdata.groupby( by= ['userId', pd.Grouper(key='time', freq='H')])['latitude','longitude'].\
    apply(get_total_harversine_distance_traveled)


#calculo la distancia total recorrida por el usuario en una hora

for index, t in s.iterrows():
    for column in ['latitudeMean', 'longitudeMean',
                   'latitudeMedian','longitudeMedian',
                   'latitudeStd','longitudeStd',
                   'place','distanceTraveled']:
        if math.isnan(t[column]):
            try:
                s.at[index, column] = s.at[(index[0], index[1] + pd.DateOffset(hours=-1)), column]
            except KeyError:
                print( 'no existe {0}'.format( (index[0], index[1])))




# prepare charge data
chargedata = pd.read_csv('processing/phonecharge.csv')
chargedata['start'] = pd.to_datetime(chargedata['start'], unit='s').dt.floor('h')
chargedata['end'] = pd.to_datetime(chargedata['end'], unit='s').dt.floor('h')

#isCharging
s['isCharging'] = False
for index, t in chargedata.iterrows() :
    for date in pd.date_range(start=t['start'], end=t['end'], freq='H'):
        try:
            s.loc[[(t['userId'], date)], 'isCharging'] = True
        except KeyError:
            pass

# prepare lock data
lockeddata = pd.read_csv('processing/phonelock.csv')
lockeddata['start'] = pd.to_datetime(lockeddata['start'], unit='s').dt.floor('h')
lockeddata['end'] = pd.to_datetime(lockeddata['end'], unit='s').dt.floor('h')


#isLocked
s['isLocked'] = False
for index, t in lockeddata.iterrows() :
    for date in pd.date_range(start=t['start'], end=t['end'], freq='H'):
        try:
            s.loc[[(t['userId'], date)], 'isLocked'] = True
        except KeyError:
            pass

# prepare dark data
darkdata = pd.read_csv('processing/dark.csv')
darkdata['start'] = pd.to_datetime(darkdata['start'], unit='s').dt.floor('h')
darkdata['end'] = pd.to_datetime(darkdata['end'], unit='s').dt.floor('h')

#isInDark
s['isInDark'] = False
for index, t in darkdata.iterrows() :
    for date in pd.date_range(start=t['start'], end=t['end'], freq='H'):
        try:
            s.loc[[(t['userId'], date)], 'isInDark'] = True
        except KeyError:
            pass



# prepare conversation data
conversationData = pd.read_csv('processing/conversation.csv')
conversationData['start_timestamp'] = pd.to_datetime(conversationData['start_timestamp'], unit='s').dt.floor('h')
conversationData[' end_timestamp'] = pd.to_datetime(conversationData[' end_timestamp'], unit='s').dt.floor('h')

#isInConversation, cantConversation
s['isInConversation'] = False
for index, t in conversationData.iterrows():
    for date in pd.date_range(start=t['start_timestamp'], end=t[' end_timestamp'], freq='H'):
        try:
            s.loc[[(t['userId'], date)], 'isInConversation'] = True
        except KeyError:
            pass

s['cantConversation'] = 0
for index, t in conversationData.iterrows():
    if t['start_timestamp'] == t[' end_timestamp']:
        try:
            s.loc[[(t['userId'], t['start_timestamp'])], 'cantConversation'] += 1
        except KeyError:
            pass
    else:
        dates = pd.date_range(start=t['start_timestamp'], end=t[' end_timestamp'], freq='H')
        for date in pd.date_range(start=t['start_timestamp'], end=t[' end_timestamp'], freq='H'):
            try:
                s.loc[[(t['userId'], date)], 'cantConversation'] += 1
            except KeyError:
                pass

#sns.lmplot('dayofweek', 'hourofday', data=s, fit_reg=False)

#sns.countplot(x='cantConversation', data=s)
'''
#cargo los datos de deadlines
deadlines = pd.read_csv('processing/deadlines.csv').iloc[:, 0:72]
deadlines = pd.melt(deadlines, id_vars='uid', var_name='time', value_name='exams')
deadlines['time'] = pd.to_datetime(deadlines['time'])
deadlines['uid'] = deadlines['uid'].str.replace('u', '', regex=True).astype('int')
deadlines = deadlines.loc[deadlines['exams'] > 0]
deadlines = deadlines.set_index('uid')


a = pd.to_datetime(max(deadlines['time']), yearfirst=True)
b = pd.to_datetime(min(deadlines['time']), yearfirst=True)
maxTime = int((a-b).total_seconds()/3600)

#beforeNextDeadline
s['beforeNextDeadline'] = 0
def getHourstoNextDeadLine(user, date):
    try: #para usuarios sobre los que no hay datos de examenes
        possibledeadlines = deadlines.loc[user, 'time']
        possibledeadlines = possibledeadlines[possibledeadlines >= date.floor('h')]
        if not possibledeadlines.empty: #para cuando no hay mas fechas de examenes
            deadline = min(possibledeadlines)
            if date.floor('h') == deadline:
                return 0
            else:
                diff = int((deadline - date).total_seconds()/3600)
            return diff
        return maxTime
    except KeyError:
        return maxTime


for ind, row in s.iterrows():
    s.at[ind, 'beforeNextDeadline'] = getHourstoNextDeadLine(ind[0], pd.to_datetime(ind[1]))

#afterLastDeadline
s['afterLastDeadline'] = 0
def getHourstoNextDeadLine(user, date):
    try: #para usuarios sobre los que no hay datos de examenes
        possibledeadlines = deadlines.loc[user, 'time']
        possibledeadlines = possibledeadlines[possibledeadlines < date.floor('h')]
        if not possibledeadlines.empty: #para cuando no hay mas fechas de examenes
            deadline = max(possibledeadlines)
            if date.floor('h') == deadline:
                return 0
            else:
                diff = int((date - deadline).total_seconds()/3600)
            return diff
        return maxTime
    except KeyError:
        return maxTime


for ind, row in s.iterrows():
    s.at[ind, 'afterLastDeadline'] = getHourstoNextDeadLine(ind[0], pd.to_datetime(ind[1]))
'''


calendardata = pd.read_csv('processing/calendar.csv')
calendardata['time'] = pd.to_datetime(calendardata['DATE'] + ' ' + calendardata['TIME'])
calendardata['time'] = calendardata['time'].dt.floor('h')
calendardata['time'] = calendardata['time']
calendardata = calendardata.set_index(['userId', 'time'])

s['hasCalendarEvent'] = False
s.loc[s.index & calendardata.index, 'hasCalendarEvent'] = True

# hay datos sobre los wifi mas cercano y ademas sobre los que el usuario estuvo
# dentro del lugar dnd estaba el wifi,
# hasta elmomento no se utilizan los datos de wifi cercanos
# se deja el wifi mas cercano, ademas de la cantidad de wifis
# a los que se conecto cada usuario en una hora, que puede ser un indicador
# de sedentarismo

wifidata = pd.read_csv('processing/wifi_location.csv')
wifidata['time'] = pd.to_datetime(wifidata['time'], unit='s').dt.floor('h')
wifidataIn = wifidata.loc[wifidata['location'].str.startswith('in')]
label_encoder = LabelEncoder()
integer_encoded = label_encoder.fit_transform(wifidataIn['location'].values)
wifidataIn['location'] = integer_encoded

#s['wifiMajor'] = 0.0
#s['wifiMajor'] = wifidataIn.groupby(['userId', 'time'])['location'].apply(Most_Common)
#s.loc[s['wifiMajor'].isna()] = 0

wifidataIn.drop_duplicates(['time', 'location', 'userId'], inplace=True)
s['wifiChanges'] = wifidataIn.groupby(['userId', 'time'])['location'].count()
s.loc[s['wifiChanges'].isna(), 'wifiChanges'] = 0
#a = wifidataIn.groupby(['userId', 'time'])['location']
#wifidataNear = wifidata.loc[wifidata['location'].str.startswith('near')]

s.to_pickle('sedentarismdata.pkl')

#swithdummies.to_pickle('sedentarism.pkl')
#checkpoint
#s.to_csv('processing/sedentaryBehaviour.csv')
#s.to_pickle('sedentarism.pkl')

