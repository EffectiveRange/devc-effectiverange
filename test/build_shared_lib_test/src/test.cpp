#include <test_shared_lib/test.hpp>
#include "test_priv.hpp"

namespace TestSharedLib
{
    int myTestFunc(int)
    {
        return TestSharedLib::val;
    }
}