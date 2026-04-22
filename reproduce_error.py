import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Simulate the data from the DB
data = {'date': ['2026-02-02'], 'amount': [0.0], 'category': ['Travel']}
df = pd.DataFrame(data)
df['date'] = pd.to_datetime(df['date'])

print("Attempting to plot lineplot...")
try:
    fig, ax = plt.subplots()
    sns.lineplot(data=df.sort_values('date'), x='date', y='amount')
    plt.fill_between(df.sort_values('date')['date'], df.sort_values('date')['amount'])
    print("Lineplot Success!")
except Exception as e:
    print(f"Lineplot caught error: {e}")

print("Attempting to plot pie...")
try:
    fig, ax = plt.subplots()
    plt.pie([0.0], labels=['Travel'])
    print("Pie Success!")
except Exception as e:
    print(f"Pie caught error: {e}")
    import traceback
    traceback.print_exc()
