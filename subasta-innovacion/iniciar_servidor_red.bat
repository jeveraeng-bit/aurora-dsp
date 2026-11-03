@echo off
title Servidor de Red - Subasta de Innovacion UAN
echo ========================================================
echo  UNIVERSIDAD ANTONIO NARINO - SEDE IBAGUE
echo  Shark Tank Inverso: La Subasta de Innovacion
echo  Expositores: Juan Esteban, Jhon Jairo, Alejandro
echo ========================================================
echo.
echo Tu direccion IP local para que tus companeros se conecten desde el celular:
for /f "tokens=4" %%a in ('route print ^| findstr 0.0.0.0.*0.0.0.0') do (
    set IP=%%a
)
ipconfig | findstr /i "IPv4"
echo.
echo Servidor iniciado en el puerto 8000.
echo Abre en el navegador de la sala: http://localhost:8000
echo O desde el celular: http://[TU_IP]:8000
echo.
python -m http.server 8000
pause
