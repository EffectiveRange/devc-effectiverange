cmake_minimum_required(VERSION 3.22)
include(ERBuild NO_POLICY_SCOPE)


project(test_sharedlib_build VERSION 1.0.0 DESCRIPTION "This is a project to test the CMAKE build & pack environment for shared libraries")


ER_DEPS()

ER_ADD_SHARED_LIBRARY(test_sharedlib SOURCES src/test.cpp)

set_property(TARGET test_sharedlib PROPERTY CXX_STANDARD 20)

target_include_directories(test_sharedlib PUBLIC include PRIVATE include_priv)

ER_PACK()

ER_ENABLE_TEST()

add_executable(unittest_sharedlib test/main.cpp)

target_link_libraries(unittest_sharedlib PRIVATE test_sharedlib)

add_test(NAME TEST_unittest_sharedlib COMMAND unittest_sharedlib )
