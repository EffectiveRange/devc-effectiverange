cmake_minimum_required(VERSION 3.22)
include(ERBuild NO_POLICY_SCOPE)

project(test_exe_build VERSION 1.0.0 DESCRIPTION "This is a project to test the CMAKE build & pack environment")


ER_DEPS()

ER_ADD_EXECUTABLE(test SOURCES test.cpp)

find_package(OpenSSL REQUIRED)

target_link_libraries(test  PRIVATE OpenSSL::SSL)


ER_PACK()