/**
 * @file RAK1906_env.cpp
 * @author Bernd Giesecke (bernd@giesecke.tk)
 * @brief BME680 sensor functions
 * @version 0.1
 * @date 2022-04-10
 *
 * @copyright Copyright (c) 2022
 *
 */
#include "main.h"
#ifndef _VARIANT_RAK3172_
#pragma message("Not RAK3172")
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

/** BME680 instance for Wire */
Adafruit_BME680 bme(&Wire);

/** Last temperature read */
float _last_bme_temp = 0;
/** Last humidity read */
float _last_bme_humid = 0;
/** Flag if values were read already (used by RAK12047 VOC sensor) */
bool _has_last_bme_values = false;

/**
 * @brief Initialize the BME680 sensor
 *
 * @return true if sensor was found
 * @return false if sensor was not found
 */
bool init_rak1906(void)
{
	Wire.begin();

	if (!bme.begin(0x76))
	{
		MYLOG("BME", "Could not find a valid BME680 sensor, check wiring!");
		return false;
	}

	// Set up oversampling and filter initialization
	bme.setTemperatureOversampling(BME680_OS_8X);
	bme.setHumidityOversampling(BME680_OS_2X);
	bme.setPressureOversampling(BME680_OS_4X);
	bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
	bme.setGasHeater(320, 150); // 320*C for 150 ms

	return true;
}

/**
 * @brief Start sensing on the BME6860
 *
 */
void start_rak1906(void)
{
	MYLOG("BME", "Start BME measuring");
	bme.beginReading();
}

/**
 * @brief Read environment data from BME680
 *     Data is added to Cayenne LPP payload as channels
 *     LPP_CHANNEL_HUMID_2, LPP_CHANNEL_TEMP_2,
 *     LPP_CHANNEL_PRESS_2 and LPP_CHANNEL_GAS_2
 *
 *
 * @return true if reading was successful
 * @return false if reading failed
 */
bool read_rak1906()
{
	MYLOG("BME", "Reading BME680");
	time_t wait_start = millis();
	bool read_success = false;
	while ((millis() - wait_start) < 5000)
	{
		if (bme.endReading())
		{
			read_success = true;
			break;
		}
	}

	if (!read_success)
	{
		MYLOG("BME", "BME reading timeout");
		return false;
	}

#if MY_DEBUG > 0
	int16_t temp_int = (int16_t)(bme.temperature * 10.0);
	uint16_t humid_int = (uint16_t)(bme.humidity * 2);
	uint16_t press_int = (uint16_t)(bme.pressure / 10);
	uint16_t gasres_int = (uint16_t)(bme.gas_resistance / 10);
#endif

	g_solution_data.addRelativeHumidity(LPP_CHANNEL_HUMID_2, bme.humidity);
	g_solution_data.addTemperature(LPP_CHANNEL_TEMP_2, bme.temperature);
	g_solution_data.addBarometricPressure(LPP_CHANNEL_PRESS_2, bme.pressure / 100);
	g_solution_data.addAnalogInput(LPP_CHANNEL_GAS_2, (float)(bme.gas_resistance) / 1000.0);

#if MY_DEBUG > 0
	MYLOG("BME", "RH= %.2f T= %.2f", bme.humidity, bme.temperature);
	MYLOG("BME", "P= %.2f R= %.2f", bme.pressure / 100.0, (float)(bme.gas_resistance) / 1000.0);
#endif

	_last_bme_humid = bme.humidity;
	_last_bme_temp = bme.temperature;
	_has_last_bme_values = true;

	return true;
}

/**
 * @brief Returns the latest values from the sensor
 *        or starts a new reading
 *
 * @param values array for temperature [0] and humidity [1]
 */
void get_rak1906_values(float *values)
{
	if (_has_last_bme_values)
	{
		_has_last_bme_values = false;
		values[0] = _last_bme_temp;
		values[1] = _last_bme_humid;
		return;
	}
	else
	{
		start_rak1906();
		delay(100);
		read_rak1906();
		values[0] = _last_bme_temp;
		values[1] = _last_bme_humid;
	}
	return;
}

/**
 * @brief Calculate and return the altitude
 *        based on the barometric pressure
 *        Requires to have MSL set
 *
 * @return uint16_t altitude in cm
 */
uint16_t get_alt_rak1906(void)
{
	// Get latest values
	start_rak1906();
	delay(250);
	if (!read_rak1906())
	{
		return 0xFFFF;
	}

	MYLOG("BME", "Compute altitude\n");
	// pressure in HPa
	float pressure = bme.pressure / 100.0;
	MYLOG("BME", "P: %.2f MSL: %.2f", bme.pressure / 100.0, mean_sea_level_press);

	float A = pressure / mean_sea_level_press; // (1013.25) by default;
	float B = 1 / 5.25588;
	float C = pow(A, B);
	C = 1.0 - C;
	C = C / 0.0000225577;
	uint16_t new_val = C * 100;
	MYLOG("BME", "Altitude: %.2f m / %d cm", C, new_val);
	return new_val;
}
#else // _VARIANT_RAK3172_
#include <rak1906.h>

#pragma message("RAK3172")

/** BME680 instance for Wire */
rak1906 bme;

/** Last temperature read */
float _last_bme_temp = 0;
/** Last humidity read */
float _last_bme_humid = 0;
/** Flag if values were read already (used by RAK12047 VOC sensor) */
bool _has_last_bme_values = false;

/**
 * @brief Initialize the BME680 sensor
 *
 * @return true if sensor was found
 * @return false if sensor was not found
 */
bool init_rak1906(void)
{
	Wire.begin();
	
	if (!bme.init())
	{
		MYLOG("BME", "Could not find a valid BME680 sensor, check wiring!");
		return false;
	}

	// Set up oversampling and filter initialization
	/// \todo Needs to be implemented in the RUI3 RAK1906 library!!!!
	bme.setOversampling(TemperatureSensor, Oversample8);
	bme.setOversampling(HumiditySensor, Oversample2);
	bme.setOversampling(PressureSensor, Oversample4);
	bme.setIIRFilter(IIR4);
	bme.setGas(320, 150); // 320*C for 150 ms

	return true;
}

/**
 * @brief Start sensing on the BME6860
 *
 */
void start_rak1906(void)
{
	// MYLOG("BME", "Start BME measuring");
	// bme.beginReading();
}

/**
 * @brief Read environment data from BME680
 *     Data is added to Cayenne LPP payload as channels
 *     LPP_CHANNEL_HUMID_2, LPP_CHANNEL_TEMP_2,
 *     LPP_CHANNEL_PRESS_2 and LPP_CHANNEL_GAS_2
 *
 *
 * @return true if reading was successful
 * @return false if reading failed
 */
bool read_rak1906()
{
	MYLOG("BME", "Reading BME680");
	// time_t wait_start = millis();
	// bool read_success = false;
	// while ((millis() - wait_start) < 5000)
	// {
	// 	if (bme.endReading())
	// 	{
	// 		read_success = true;
	// 		break;
	// 	}
	// }

	if (!bme.update())
	{
		MYLOG("BME", "BME reading timeout");
		return false;
	}

#if MY_DEBUG > 0
	int16_t temp_int = (int16_t)(bme.temperature() * 10.0);
	uint16_t humid_int = (uint16_t)(bme.humidity() * 2);
	uint16_t press_int = (uint16_t)(bme.pressure() / 10);
	uint16_t gasres_int = (uint16_t)(bme.gas() / 10);
#endif

	g_solution_data.addRelativeHumidity(LPP_CHANNEL_HUMID_2, bme.humidity());
	g_solution_data.addTemperature(LPP_CHANNEL_TEMP_2, bme.temperature());
	g_solution_data.addBarometricPressure(LPP_CHANNEL_PRESS_2, bme.pressure());
	g_solution_data.addAnalogInput(LPP_CHANNEL_GAS_2, (float)(bme.gas()) / 1000.0);

#if MY_DEBUG > 0
	MYLOG("BME", "RH= %.2f T= %.2f", bme.humidity(), bme.temperature());
	MYLOG("BME", "P= %.2f R= %.2f", bme.pressure(), (float)(bme.gas()) / 1000.0);
#endif

	_last_bme_humid = bme.humidity();
	_last_bme_temp = bme.temperature();
	_has_last_bme_values = true;

	return true;
}

/**
 * @brief Returns the latest values from the sensor
 *        or starts a new reading
 *
 * @param values array for temperature [0] and humidity [1]
 */
void get_rak1906_values(float *values)
{
	if (_has_last_bme_values)
	{
		_has_last_bme_values = false;
		values[0] = _last_bme_temp;
		values[1] = _last_bme_humid;
		return;
	}
	else
	{
		// start_rak1906();
		// delay(100);
		read_rak1906();
		values[0] = _last_bme_temp;
		values[1] = _last_bme_humid;
	}
	return;
}

/**
 * @brief Calculate and return the altitude
 *        based on the barometric pressure
 *        Requires to have MSL set
 *
 * @return uint16_t altitude in cm
 */
uint16_t get_alt_rak1906(void)
{
	// Get latest values
	// start_rak1906();
	// delay(250);
	if (!read_rak1906())
	{
		return 0xFFFF;
	}

	MYLOG("BME", "Compute altitude\n");
	// pressure in HPa
	float pressure = bme.pressure() / 100.0;
	MYLOG("BME", "P: %.2f MSL: %.2f", bme.pressure() / 100.0, mean_sea_level_press);

	float A = pressure / mean_sea_level_press; // (1013.25) by default;
	float B = 1 / 5.25588;
	float C = pow(A, B);
	C = 1.0 - C;
	C = C / 0.0000225577;
	uint16_t new_val = C * 100;
	MYLOG("BME", "Altitude: %.2f m / %d cm", C, new_val);
	return new_val;
}
#endif // _VARIANT_RAK3172_