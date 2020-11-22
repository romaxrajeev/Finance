import datetime
import math
date = datetime.datetime.now()  
month=int(date.strftime('%m'))
salary=eval(input('Enter monthly salary: '))
goal_name=input('Enter the goal name: ')
amount=eval(input('Enter the amount to be invested: '))
invest_time=eval(input('Enter the time for which investment is to be done: '))
expectedSaving=amount//invest_time
print('Investment to be done every month: ',expectedSaving)
saving=0
s=0
while(saving<amount):
    print('')
    expenditure=eval(input('Enter the monthly expenditure: '))
    monthlySavings=salary-expenditure
    s+=expectedSaving
    saving+=monthlySavings
    percent=math.ceil((saving/amount)*100)
    print('Expenditure\tMonthly Saving\t\tTotal Savings')
    print(expenditure,'\t\t',monthlySavings,'\t\t',saving)
    print(percent,"%")
    if(saving>=s):
        print('Congratulations, You are on track to achieve your goal.')
    else:
        print('Oops. Extra Expenditure. Save ',s-saving,' more in the next month')
    
#date: current date
#month: current month
#salary: monthly salary
#amount: investment amount
#invest_time: time in which goal is to be achieved
#expectedSaving: how much minimum savings should be done to achieve goal in 'invest_time'
#expenditure: monthly expenditure
#monthlySavings: money saved each month(salary-expenditure)
#saving: total savings made
#s: how much is savings should be made be i'th iteration
''' s-saving gives lagging of the investment '''
