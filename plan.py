import pandas as pd
import datetime as dt
from plan_indicat import ind
import pickle
from user_data import *
from handle_data import handler
import pytz
import os

risk = MAX_PERCENTAGE_ACCOUNT_AT_RISK
capital = float(handler().account_balance())
daily_risk = capital * risk
ind = ind()

trade_short = ['USDJPY', 'GBPJPY', 'AUDJPY'] 
trade_long = ['USDCAD', 'IBUS500', 'EURUSD', 'IBJP225'] 

class build_plan:

        def __init__(self):
                self.handler = handler()
                self.assets = handler().assets



        def _get_new_data(self):
                if 'IB' not in os.listdir('./../DATA/'):
                        last = dt.datetime.now(tz=pytz.timezone("Europe/Moscow")).date() - dt.timedelta(1900)
                        db = pd.DataFrame()
                else:
                        db = pd.read_pickle('./../DATA/IB') 
                        db.columns = db.columns.str.lower()
                        db = db[db.index < sorted(db.index.unique())[-1]]

                        db = db.reset_index().set_index('date')
                        last = sorted(db.index.unique())[-1].date()
                        

                data = pd.DataFrame()

                if last == (dt.datetime.now(tz=pytz.timezone("Europe/Moscow")).date()):
                        pass
                else:
                        total = int(str(dt.datetime.now(tz=pytz.timezone("Europe/Moscow")).date()-last).split(' ')[0])

                        for i in self.assets.keys(): 
                                df = self.handler.candle_data(i, 1440, total) 

                                data = pd.concat([data, df], sort=True).drop_duplicates()

                        data = data.set_index(['date', 'asset'])
                        if len(db) > 1:
                                db = db.reset_index().set_index(['date', 'asset'])
                                data = pd.concat([db, data], sort=True).drop_duplicates()

                        
                        data = data.reset_index().set_index('date')


                        self._remove_duplicated(data)
                


        def _remove_duplicated(self, df):

                df = df.reset_index()
                db = pd.DataFrame()

                for i in df.asset.unique():
                        data = df[df.asset == i]      
                        pd.DataFrame.drop_duplicates(data, subset='date', inplace=True)  
                        db = pd.concat([db, data], sort=True)

                db = db.set_index('date')

                pd.DataFrame.sort_index(db, inplace=True)

                db = db[db.index < sorted(db.index.unique())[-1]]
                db = db.dropna()

                db.to_pickle('./../DATA/IB') 

                ### OPTIONAL TO RUN PLAN ONLY ON THOSE ASSETS
                db = db[db.asset.isin(['EURUSD', 'EURAUD', 'GBPJPY', 'GBPCAD', 'USDCAD', 'USDJPY', 'AUDJPY', 'IBUS500',
                                        'IBUST100', 'IBGB100', 'IBDE30', 'IBFR40', 'IBJP225', 'IBHK50', 'IBAU200'])]

                ind.indicador(db)
                
                

        def run_daily(self):
                self._get_new_data()

                db = pd.read_pickle('./../DATA/IB_OHLC') #UP-
                db = db.dropna()
                db = db[db.index == db.index[-1]]

                ### ADD THE IDEA BEHIND THE BUILDING DAY PLAN ###
		### HERE JUST A SIMPLE EXAMPLE OF RANDOM LONG-SHORT ###
		
		ltm = db[db.asset.isin(trade_short)]
                ltm['strat'] = 'trade_short'

                ltp = db[db.asset.isin(trade_long)]
                ltp['strat'] = 'trade_long'

                ### EASY ADAPT, CHANGE DB.CLOSE <> DB.SMA20 or OTHER OPTIONS THAT ARE INSIDE PLAN_INDICAT.PY 
                SMA20_SMA200_UP = db[db.SMA20 > db.SMA200]
                SMA20_SMA200_UP['strat'] = 'SMA20_SMA200_UP'

                SMA20_SMA200_DOWN = db[db.SMA20 < db.SMA200]
                SMA20_SMA200_DOWN['strat'] = 'SMA20_SMA200_DOWN'

		trade = pd.concat([ltm, ltp])
		trade.index = trade.index + dt.timedelta(1)
		
                plano = {}
                total_try = []

                for i in range(len(trade)):
                        atr = trade.iloc[i].ATR
                        trading_hours = [900, 2000]
                        break_lunch = [1200, 1400]
                        profit = [2, 30, 100, 'day']
                        stop = [1, 30, 100, 'day']
                        duration = pd.to_datetime(120, unit='m').time()
                        try_qty = 3
                        strat_cond = 'and'

                        if trade.iloc[i].strat == 'trade_short':
                                direction = 'sell'
                                strat = {'strat2': 5}
                                strat_name = 'trade_short'
                                try_qty = 3
                                strat_cond = 'and'

                        elif trade.iloc[i].strat == 'trade_long':
                                direction = 'buy'
                                strat = {'strat2': 5}
                                strat_name = 'trade_long'
                                try_qty = 3
                                strat_cond = 'and'

                        if trade.iloc[i].strat == 'SMA20_SMA200_DOWN':
                                direction = 'sell'
                                strat = {'strat2': 5}
                                strat_name = 'SMA20_SMA200_DOWN'
                                try_qty = 3
                                strat_cond = 'and'

                        elif trade.iloc[i].strat == 'SMA20_SMA200_UP':
                                direction = 'buy'
                                strat = {'strat2': 5}
                                strat_name = 'SMA20_SMA200_UP'
                                try_qty = 3
                                strat_cond = 'and'


                        else:
                                pass

                        total_try.append(try_qty)


                        plano.update({trade.iloc[i].asset+'_'+str(i):
                                        {'asset': trade.iloc[i].asset, 'direction': direction, 'size': 0, 'profit': profit, 'stop': stop, 'start': trading_hours[0], 'end': trading_hours[1], 'duration': duration, 'try_qty': try_qty,
                                        'strat': strat, 'strat_cond': strat_cond, 'strat_name': strat_name, 'atr': atr, 'break_start': break_lunch[0], 'break_end': break_lunch[1]}
                                        })


                if len(plano.keys()) > 0:
                        size = int(daily_risk / len(plano.keys())) #sum(total_try) #UPGRADED
                else:
                        size = 0

                for i in plano:
                        plano.get(i).update({
                                'size': size
                        })


                with open(f'./DATA/plan/plan_{dt.datetime.now(tz=pytz.timezone("Europe/Moscow")).date()}', 'wb') as file:
                        pickle.dump(plano, file, protocol=pickle.HIGHEST_PROTOCOL)


                print(pd.DataFrame(plano.values(), plano.keys()))






