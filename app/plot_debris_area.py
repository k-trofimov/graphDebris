from datetime import datetime

import numpy as np
from dateutil.relativedelta import relativedelta
from matplotlib.figure import Figure


def plot_debris_area(data):
    # Sort the list based on the month_year
    print(data)
    data = sorted(data, key=lambda x: x[0])

    # Get the x and y data
    x = [int(i.split("_")[0]) for i, j in data]

    y = [j for i, j in data]

    # Fit a line to the data using numpy's polyfit
    coefficients = np.polyfit(x, y, 1)

    # Get the equation for the line
    line = np.poly1d(coefficients)

    # Predict the next month
    x_h = [datetime.strptime(i, "%m_%Y") for i, j in data]

    prediction = line(max(x) + 1)
    # Plot the data and prediction
    plt = Figure()

    plt.set_figwidth(10)
    axis = plt.add_subplot(1, 1, 1)
    axis.plot(x_h, y, "ro")
    axis.plot(x_h, y, "-b")
    axis.plot(
        [x_h[-1], max(x_h) + relativedelta(months=+1)], [y[-1], line(max(x) + 1)], "-r"
    )

    axis.set_xlabel("Month")
    axis.set_ylabel("Area (m^2)")
    axis.set_title("Debris Surface Area Evolution")
    axis.grid()

    return plt
