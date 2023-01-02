/**
 * @file custom_at.cpp
 * @author Bernd Giesecke (bernd@giesecke.tk)
 * @brief
 * @version 0.1
 * @date 2022-05-12
 *
 * @copyright Copyright (c) 2022
 *
 */
#include "main.h"

// Forward declarations
int interval_send_handler(SERIAL_PORT port, char *cmd, stParam *param);
int status_handler(SERIAL_PORT port, char *cmd, stParam *param);

uint32_t g_send_repeat_time = 0;

/**
 * @brief Add send interval AT command
 *
 * @return true if success
 * @return false if failed
 */
bool init_interval_at(void)
{
	return api.system.atMode.add((char *)"SENDINT",
								 (char *)"Set/Get the interval sending time values in seconds 0 = off, max 2,147,483 seconds",
								 (char *)"SENDINT", interval_send_handler);
}

/**
 * @brief Handler for send interval AT commands
 *
 * @param port Serial port used
 * @param cmd char array with the received AT command
 * @param param char array with the received AT command parameters
 * @return int result of command parsing
 * 			AT_OK AT command & parameters valid
 * 			AT_PARAM_ERROR command or parameters invalid
 */
int interval_send_handler(SERIAL_PORT port, char *cmd, stParam *param)
{
	if (param->argc == 1 && !strcmp(param->argv[0], "?"))
	{
		Serial.print(cmd);
		Serial.printf("=%lds\r\n", g_send_repeat_time / 1000);
	}
	else if (param->argc == 1)
	{
		MYLOG("AT_CMD", "param->argv[0] >> %s", param->argv[0]);
		for (int i = 0; i < strlen(param->argv[0]); i++)
		{
			if (!isdigit(*(param->argv[0] + i)))
			{
				MYLOG("AT_CMD", "%d is no digit", i);
				return AT_PARAM_ERROR;
			}
		}

		uint32_t new_send_freq = strtoul(param->argv[0], NULL, 10);

		MYLOG("AT_CMD", "Requested interval %ld", new_send_freq);

		g_send_repeat_time = new_send_freq * 1000;

		MYLOG("AT_CMD", "New interval %ld", g_send_repeat_time);
		// Stop the timer
		api.system.timer.stop(RAK_TIMER_0);
		if (g_send_repeat_time != 0)
		{
			// Restart the timer
			api.system.timer.start(RAK_TIMER_0, g_send_repeat_time, NULL);
		}
		// Save custom settings
		save_at_setting();
	}
	else
	{
		return AT_PARAM_ERROR;
	}

	return AT_OK;
}

/**
 * @brief Add custom Status AT commands
 *
 * @return true AT commands were added
 * @return false AT commands couldn't be added
 */
bool init_status_at(void)
{
	return api.system.atMode.add((char *)"STATUS",
								 (char *)"Get device information",
								 (char *)"STATUS", status_handler);
}

/** Regions as text array */
char *regions_list[] = {"EU433", "CN470", "RU864", "IN865", "EU868", "US915", "AU915", "KR920", "AS923", "AS923-2", "AS923-3", "AS923-4"};
/** Network modes as text array*/
char *nwm_list[] = {"P2P", "LoRaWAN", "FSK"};

/**
 * @brief Print device status over Serial
 *
 * @param port Serial port used
 * @param cmd char array with the received AT command
 * @param param char array with the received AT command parameters
 * @return int result of command parsing
 * 			AT_OK AT command & parameters valid
 * 			AT_PARAM_ERROR command or parameters invalid
 */
int status_handler(SERIAL_PORT port, char *cmd, stParam *param)
{
	String value_str = "";
	int nw_mode = 0;
	int region_set = 0;
	uint8_t key_eui[16] = {0}; // efadff29c77b4829acf71e1a6e76f713

	if (param->argc == 1 && !strcmp(param->argv[0], "?"))
	{
		Serial.println("Device Status:");
		/// \todo old API call
		value_str = api.system.modelId.get();
		/// \todo new API call
		// value_str = api.system.hwModel.get();
		value_str.toUpperCase();
		Serial.printf("Module: %s\r\n", value_str.c_str());
		/// \todo old API call
		Serial.printf("Version: %s\r\n", api.system.firmwareVersion.get().c_str());
		/// \todo new API call
		// Serial.printf("Version: %s\r\n", api.system.firmwareVer.get().c_str());
		Serial.printf("Send time: %d s\r\n", g_send_repeat_time / 1000);
		nw_mode = api.lorawan.nwm.get();
		Serial.printf("Network mode %s\r\n", nwm_list[nw_mode]);
		if (nw_mode == 1)
		{
			Serial.printf("Network %s\r\n", api.lorawan.njs.get() ? "joined" : "not joined");
			region_set = api.lorawan.band.get();
			Serial.printf("Region: %d\r\n", region_set);
			Serial.printf("Region: %s\r\n", regions_list[region_set]);
			if (api.lorawan.njm.get())
			{
				Serial.println("OTAA mode");
				api.lorawan.deui.get(key_eui, 8);
				Serial.printf("DevEUI = %02X%02X%02X%02X%02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3],
							  key_eui[4], key_eui[5], key_eui[6], key_eui[7]);
				api.lorawan.appeui.get(key_eui, 8);
				Serial.printf("AppEUI = %02X%02X%02X%02X%02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3],
							  key_eui[4], key_eui[5], key_eui[6], key_eui[7]);
				api.lorawan.appkey.get(key_eui, 16);
				Serial.printf("AppKey = %02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3],
							  key_eui[4], key_eui[5], key_eui[6], key_eui[7],
							  key_eui[8], key_eui[9], key_eui[10], key_eui[11],
							  key_eui[12], key_eui[13], key_eui[14], key_eui[15]);
			}
			else
			{
				Serial.println("ABP mode");
				api.lorawan.appskey.get(key_eui, 16);
				Serial.printf("AppsKey = %02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3],
							  key_eui[4], key_eui[5], key_eui[6], key_eui[7],
							  key_eui[8], key_eui[9], key_eui[10], key_eui[11],
							  key_eui[12], key_eui[13], key_eui[14], key_eui[15]);
				api.lorawan.nwkskey.get(key_eui, 16);
				Serial.printf("NwsKey = %02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3],
							  key_eui[4], key_eui[5], key_eui[6], key_eui[7],
							  key_eui[8], key_eui[9], key_eui[10], key_eui[11],
							  key_eui[12], key_eui[13], key_eui[14], key_eui[15]);
				api.lorawan.daddr.set(key_eui, 4);
				Serial.printf("DevAddr = %02X%02X%02X%02X\r\n",
							  key_eui[0], key_eui[1], key_eui[2], key_eui[3]);
			}
		}
		else if (nw_mode == 0)
		{
			Serial.printf("Frequency = %d\r\n", api.lorawan.pfreq.get());
			Serial.printf("SF = %d\r\n", api.lorawan.psf.get());
			Serial.printf("BW = %d\r\n", api.lorawan.pbw.get());
			Serial.printf("CR = %d\r\n", api.lorawan.pcr.get());
			Serial.printf("Preamble length = %d\r\n", api.lorawan.ppl.get());
			Serial.printf("TX power = %d\r\n", api.lorawan.ptp.get());
		}
		else
		{
			Serial.printf("Frequency = %d\r\n", api.lorawan.pfreq.get());
			Serial.printf("Bitrate = %d\r\n", api.lorawan.pbr.get());
			Serial.printf("Deviaton = %d\r\n", api.lorawan.pfdev.get());
		}
	}
	else
	{
		return AT_PARAM_ERROR;
	}
	return AT_OK;
}

/**
 * @brief Get setting from flash
 *
 * @return false read from flash failed or invalid settings type
 */
bool get_at_setting(void)
{
	uint8_t flash_value[16];
	if (!api.system.flash.get(SEND_FREQ_OFFSET, flash_value, 5))
	{
		MYLOG("AT_CMD", "Failed to read send interval from Flash");
		return false;
	}
	if (flash_value[4] != 0xAA)
	{
		MYLOG("AT_CMD", "No valid send interval found, set to default, read 0X%02X 0X%02X 0X%02X 0X%02X",
			  flash_value[0], flash_value[1],
			  flash_value[2], flash_value[3]);
		g_send_repeat_time = 0;
		save_at_setting();
		return false;
	}
	MYLOG("AT_CMD", "Read send interval 0X%02X 0X%02X 0X%02X 0X%02X",
		  flash_value[0], flash_value[1],
		  flash_value[2], flash_value[3]);
	g_send_repeat_time = 0;
	g_send_repeat_time |= flash_value[0] << 0;
	g_send_repeat_time |= flash_value[1] << 8;
	g_send_repeat_time |= flash_value[2] << 16;
	g_send_repeat_time |= flash_value[3] << 24;
	MYLOG("AT_CMD", "Send interval found %ld", g_send_repeat_time);
	return true;
}

/**
 * @brief Save setting to flash
 *
 * @return true write to flash was successful
 * @return false write to flash failed or invalid settings type
 */
bool save_at_setting(void)
{
	uint8_t flash_value[16] = {0};
	bool wr_result = false;
	flash_value[0] = (uint8_t)(g_send_repeat_time >> 0);
	flash_value[1] = (uint8_t)(g_send_repeat_time >> 8);
	flash_value[2] = (uint8_t)(g_send_repeat_time >> 16);
	flash_value[3] = (uint8_t)(g_send_repeat_time >> 24);
	flash_value[4] = 0xAA;
	MYLOG("AT_CMD", "Writing send interval 0X%02X 0X%02X 0X%02X 0X%02X ",
		  flash_value[0], flash_value[1],
		  flash_value[2], flash_value[3]);
	wr_result = api.system.flash.set(SEND_FREQ_OFFSET, flash_value, 5);
	if (!wr_result)
	{
		// Retry
		wr_result = api.system.flash.set(SEND_FREQ_OFFSET, flash_value, 5);
	}
	wr_result = true;
	return wr_result;
}
