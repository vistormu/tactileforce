# from udp to a real-time plot

this small python util is for plotting time-series data from a udp stream

## installation

clone the repository and install the dependencies with pip:

```bash
git clone https://github.com/vistormu/udp2plot.git
cd udp2plot
```

```bash
pip install -r requirements.txt
```

> [!NOTE]
> this script requires python 3.10 or higher

## usage

- the main idea behind this project is to be able to plot the information from peripherals, which are sending data through udp

- there will be only one client at a time, and when it disconnects, it stops the plot and saves the data sent

- the data will be saved with all the information sent by the client, including the ones that are not plotted

- the filename of the saved data will be the current date and time in the format specified in the config file

create a file called `config.toml` in the root directory of the project and fill it with the following content:

### server config

- ip: the ip address of the server. you can use `auto` to automatically detect the ip address
- port: the port number of the server
- timeout: the amount of time to consider as a client disconnect

```toml
[server]
ip = "auto"
port = 8080
timeout = 2 # seconds
```

### data config

- save: whether to save the data or not
- path: the path to save the data. if the path does not exist, it will raise a warning and not save the data
- date_format: the format of the date and time to save the data

```toml
[data]
save = false
path = "path/to/save/data"
date_format = "%d-%m-%Y_%H-%M-%S"
```

### figure config

- save: whether to save the figure or not
- path: the path to save the figure. if the path does not exist, it will raise a warning and not save the figure
- format: the format of the figure
- date_format: the format of the date and time to save the figure

```toml
[figure]
save = false
path = "figures/"
format = "png"
date_format = "%d-%m-%Y_%H-%M-%S"
```

### colors config

you can (must) define the colors of the lines in the plot 

```toml
[colors]
red = "#cf7171"
green = "#dbe8c1"
blue = "#aecdd2"
yellow = "#fadf7f"
purple = "#c696bc"
black = "#4d5359"
```

### plot config

- layout: the layout of the plot. it can be `1x1`, `1x2`, `2x1`...
- time_window: the time window of the plot in second. outside of this window, the data will be discarded
- dt: the time step of the plot in second. it is a placeholder value to calculate the number of points to plot. may be removed in the future
- size: the size of the plot in inches
- padding: the top and bottom padding added to the limits of the plot. it is a percentage of the data range

```toml
[plot]
layout = "2x2"
time_window = 30 # seconds
dt = 0.01 # s
size = [14, 8] # inches
padding = 5 # percentage
```

to add plots to the specified layout, the keys of the plot config must be in the format of `plot."(<row>,<column>)"`

- x: the name of the data to plot on the x-axis
- y: the names of the data to plot on the y-axis
- colors: the colors of the lines in the plot. should match the colors defined in the colors config
- xlabel: the label of the x-axis
- ylabel: the label of the y-axis
- limits: the limits of the plot
- title: the title of the plot
- n_ticks: the number of ticks on the y-axis

for example, to add a plot to the first row and the first column, you must add a key called `plot."(1,1)"`:

```toml
[plot."(1,1)"]
x = "time"
y = ["fx", "fy", "fz"]
colors = ["red", "green", "blue"]
xlabel = "time (s)"
ylabel = "force (N)"
limits = [-2, 2]
title = "force"
n_ticks = 10
```

you can also set a plot to cover multiple rows or columns using python notation: `plot."(:,1)`

### multiple configs

in this project, i have multiple configs under the `configs` directory. you can use them by passing the name of the config file as an argument to the script:

```bash
python main.py --config path/to/config.toml
```
