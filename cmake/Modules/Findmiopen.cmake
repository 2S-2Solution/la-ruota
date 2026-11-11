# [VEGA-PATCH 8 T09:14] Stub Findmiopen.cmake per Windows ROCm
# MIOpen su Windows TheRock build separato, config non distribuito.
set(miopen_FOUND TRUE)
set(miopen_VERSION "3.4.0")
set(miopen_LIBRARIES "MIOpen")
set(miopen_INCLUDE_DIRS "C:/TheRock_workspace/TheRock/build_gfx906/artifacts/miopen_run_generic/ml-libs/MIOpen/stage/include")
if(NOT TARGET MIOpen)
  add_library(MIOpen INTERFACE IMPORTED)
endif()
