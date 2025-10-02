@echo off
echo Compiling video_functions.c to DLL...
echo.

echo Attempting compilation with Visual Studio (cl.exe)...
cl /LD video_functions.c /Fe:video_functions.dll 2>nul

if exist video_functions.dll (
    echo SUCCESS: video_functions.dll created successfully!
    echo.
    echo The video processing functionality is now available.
    goto :end
)

echo Visual Studio compiler not found. Trying MinGW-w64...
gcc -shared -fPIC -o video_functions.dll video_functions.c 2>nul

if exist video_functions.dll (
    echo SUCCESS: video_functions.dll created successfully with GCC!
    echo.
    echo The video processing functionality is now available.
    goto :end
)

echo.
echo ERROR: Could not compile video_functions.dll
echo.
echo Please ensure you have one of the following installed:
echo - Visual Studio with C++ tools
echo - MinGW-w64 with GCC
echo.
echo You can also manually compile using:
echo   cl /LD video_functions.c /Fe:video_functions.dll
echo   OR
echo   gcc -shared -fPIC -o video_functions.dll video_functions.c

:end
echo.
echo Press any key to continue...
pause >nul