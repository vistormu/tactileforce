# tactileforce

hi! welcome to the repo of my research during my phd stay at TU Delft from january to april 2025

the line of research consisted of a tactile sensor made in-house with a deformable cap on top. the main idea is to use this sensor as a substitute of force-torque sensors, which are usually expensive and heavy.

i created two applications:

- using the sensor as an electronic skin. for more information, check the [skin dir](./skin/) of this repo.

- online learning of the forces after grasping. the robot grasps an object and you teach it to "feel" the forces on real time. then the robot follows you around.

for the latter, i had to create three different programs:

- [`raspberry`](./raspberry/): it contains the code for reading, filtering, and sending the sensor's data
- [`desktop`](./desktop/): it receives the sensor's data, trains the model, and plots de data and the prediction, all in real time. then, it sends the force prediction to a ros node. as i  am using a macbook, i couldn't install ros.
- [`ros`](./ros/): the code for the computer running ros. it receives the force predictions and moves the robot accordingly

check out the README files of the rest of the directories for a deeper explanation
