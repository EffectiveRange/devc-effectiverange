cmake_minimum_required(VERSION 3.22)
include(ERBuild NO_POLICY_SCOPE)

project(test_complex_build VERSION 1.0.0 DESCRIPTION "This is a complex project to test the CMAKE build & pack environment")


ER_DEPS()

add_subdirectory(testlib)

add_subdirectory(testbin)

ER_PACK()