cmake_minimum_required(VERSION 2.8.3)
project(camera_recorder)
find_package(catkin REQUIRED COMPONENTS
  message_generation
  rospy
  std_srvs
)

## Generate services in the 'srv' folder
add_service_files(
  FILES
  Configure.srv
  Record.srv
)

## Generate added messages and services with any dependencies listed here
generate_messages()

catkin_package(
  CATKIN_DEPENDS std_srvs message_runtime
)

## Add folders to be run by python nosetests
# catkin_add_nosetests(test)
