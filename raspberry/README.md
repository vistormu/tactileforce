# raspberry

this is the code related to the data acquisition for the force-torque sensor and the tactile sensor

## sensors

### torque-force sensor

The torque-force sensor used is a [SensOne](https://www.botasys.com/force-torque-sensors/sensone) sensor from Bota systems.

The communication is done via the serial port through a USB connection.

The data collected from the sensor is a 6x1 vector with the following information:
- `Fx` - force in the x direction
- `Fy` - force in the y direction
- `Fz` - force in the z direction
- `Tx` - torque in the x direction
- `Ty` - torque in the y direction
- `Tz` - torque in the z direction

### tactile sensor

The tactile sensor is made in-house at TU Delft. 

0 = ADC_0  
1 = ADC_1  
2 = ADC_2  
3 = ADC_3  
10 = Used to switch LEDs on and off  
  
Red = 3v3  
Black = Ground  
Brown = Sensor 0  
Purple = Sensor 1  
Yellow = Sensor 2  
Green = Sensor 3  
Blue = Potentiometer (0-2000 Ohm)  
Orange = LED switch (0:off, 1:on)  


### ADC


### potentiometer


## installation on a raspberry pi

### install go

### enable interfaces

### install conda

## running the code

Build the code

```
ln -s go TMP
```


## show the IP on boot

run

```
make startup
```

and add the following line

```
@reboot /home/raspberry/projects/tactileforce/startup/startup.sh
```
