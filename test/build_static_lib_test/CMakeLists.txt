cmake_minimum_required(VERSION 3.22)
include(ERBuild NO_POLICY_SCOPE)

project(test_staticlib_build VERSION 1.0.0 DESCRIPTION "This is a project to test the CMAKE build & pack environment for static libraries")


ER_DEPS()

ER_ADD_STATIC_LIBRARY(test_slib SOURCES src/test.cpp)

set_property(TARGET test_slib PROPERTY CXX_STANDARD 20)

target_include_directories(test_slib PUBLIC include PRIVATE include_priv)

ER_PACK()