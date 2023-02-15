/**
 * @file RUI3-Modular.ino
 * @author Bernd Giesecke (bernd@giesecke.tk)
 * @brief RUI3 based code for easy testing of WisBlock I2C modules
 * @version 0.1
 * @date 2022-10-29
 *
 * @copyright Copyright (c) 2022
 *
 */
#include "main.h"

/** Initialization results */
bool ret;

/** LoRaWAN packet */
WisCayenne g_solution_data(255);

/** Packet is confirmed/unconfirmed (Set with AT commands) */
bool g_confirmed_mode = false;
/** If confirmed packet, number or retries (Set with AT commands) */
uint8_t g_confirmed_retry = 0;
/** Data rate  (Set with AT commands) */
uint8_t g_data_rate = 3;

/** Flag if transmit is active, used by some sensors */
volatile bool tx_active = false;

/** fPort to send packages */
uint8_t set_fPort = 2;

/** Enable automatic DR selection based on payload size */
#if AUTO_DR == 1
bool auto_dr_enabled = true;
#else
bool auto_dr_enabled = false;
#endif

/**
 * @brief Callback after packet was received
 *
 * @param data Structure with the received data
 */
void receiveCallback(SERVICE_LORA_RECEIVE_T *data)
{
	MYLOG("RX-CB", "RX, port %d, DR %d, RSSI %d, SNR %d", data->Port, data->RxDatarate, data->Rssi, data->Snr);
	for (int i = 0; i < data->BufferSize; i++)
	{
		Serial.printf("%02X", data->Buffer[i]);
	}
	Serial.print("\r\n");

	/*************************************************/
	/*************************************************/
	/** Insert here sensor specific downlink handler */
	/*************************************************/
	/*************************************************/
	// if ((gnss_format == FIELD_TESTER) && (data->Port == 2))
	// {
	// 	int16_t min_rssi = data->Buffer[1] - 200;
	// 	int16_t max_rssi = data->Buffer[2] - 200;
	// 	int16_t min_distance = data->Buffer[3] * 250;
	// 	int16_t max_distance = data->Buffer[4] * 250;
	// 	int8_t num_gateways = data->Buffer[5];
	// 	Serial.printf("+EVT:FieldTester %d gateways\n", num_gateways);
	// 	Serial.printf("+EVT:RSSI min %d max %d\n", min_rssi, max_rssi);
	// 	Serial.printf("+EVT:Distance min %d max %d\n", min_distance, max_distance);
	// }
}

/**
 * @brief Callback after TX is finished
 *
 * @param status TX status
 */
void sendCallback(int32_t status)
{
	MYLOG("TX-CB", "TX status %d", status);
	digitalWrite(LED_BLUE, LOW);
	/***********************************************/
	/***********************************************/
	/** Insert here sensor specific initialization */
	/***********************************************/
	/***********************************************/
#ifdef _RAK12500_GNSS_H_
	gnss_active = false;
#endif
	tx_active = false;
}

/**
 * @brief Callback after join request cycle
 *
 * @param status Join result
 */
void joinCallback(int32_t status)
{
	// MYLOG("JOIN-CB", "Join result %d", status);
	if (status != 0)
	{
		MYLOG("JOIN-CB", "LoRaWan OTAA - join fail! \r\n");
		// To be checked if this makes sense
		// api.lorawan.join();
	}
	else
	{
		// bool result_set = api.lorawan.dr.set(g_data_rate);
		// MYLOG("JOIN-CB", "Set the data rate  %s", result_set ? "Success" : "Fail");
		MYLOG("JOIN-CB", "LoRaWan OTAA - joined! \r\n");
		digitalWrite(LED_BLUE, LOW);
	}
}

/**
 * @brief Arduino setup, called once after reboot/power-up
 *
 */
void setup()
{
	if (api.lorawan.nwm.get() == 1)
	{
		g_confirmed_mode = api.lorawan.cfm.get();

		g_confirmed_retry = api.lorawan.rety.get();

		g_data_rate = api.lorawan.dr.get();

		// Setup the callbacks for joined and send finished
		api.lorawan.registerRecvCallback(receiveCallback);
		api.lorawan.registerSendCallback(sendCallback);
		api.lorawan.registerJoinCallback(joinCallback);
	}

	pinMode(LED_GREEN, OUTPUT);
	digitalWrite(LED_GREEN, HIGH);
	pinMode(LED_BLUE, OUTPUT);
	digitalWrite(LED_BLUE, HIGH);

	pinMode(WB_IO2, OUTPUT);
	digitalWrite(WB_IO2, HIGH);

	// Start Serial
	Serial.begin(115200);

// #ifdef _VARIANT_RAK4630_
// 	time_t serial_timeout = millis();
// 	// On nRF52840 the USB serial is not available immediately
// 	// while (!Serial.available())
// 	while (!Serial)
// 	{
// 		if ((millis() - serial_timeout) < 15000)
// 		{
// 			delay(100);
// 			digitalWrite(LED_GREEN, !digitalRead(LED_GREEN));
// 		}
// 		else
// 		{
// 			break;
// 		}
// 	}
// #else
// 	// For RAK3172 just wait a little bit for the USB to be ready
// 	delay(5000);
// #endif

	// Delay for 5 seconds to give the chance for AT+BOOT
	delay(5000);

	Serial.println("RAKwireless RUI3 Node");
	Serial.println("------------------------------------------------------");
	Serial.println("Setup the device with WisToolBox or AT commands before using it");
	Serial.println("------------------------------------------------------");

	/* Initialize sensor modules */
	init_modules();

	// Register the custom AT command to get device status
	if (!init_status_at())
	{
		MYLOG("SETUP", "Add custom AT command STATUS fail");
	}
	digitalWrite(LED_GREEN, LOW);

	// Register the custom AT command to set the send interval
	if (!init_interval_at())
	{
		MYLOG("SETUP", "Add custom AT command Send Interval fail");
	}

	// Get saved sending interval from flash
	get_at_setting();

	// Create a timer.
	api.system.timer.create(RAK_TIMER_0, sensor_handler, RAK_TIMER_PERIODIC);
	if (g_send_repeat_time != 0)
	{
		// Start a timer.
		api.system.timer.start(RAK_TIMER_0, g_send_repeat_time, NULL);
	}

	if (api.lorawan.nwm.get() == 0)
	{
		digitalWrite(LED_BLUE, LOW);

		sensor_handler(NULL);
	}
#if MY_DEBUG == 0
	MYLOG("SETUP", "Debug is disabled");
#else
	MYLOG("SETUP", "Debug is enabled");
#endif
#if AUTO_DR == 0
	MYLOG("SETUP", "Auto DR is disabled");
#else
	MYLOG("SETUP", "Auto DR is enabled");
#endif

	if (api.lorawan.nwm.get() == 1)
	{
		if (g_confirmed_mode)
		{
			MYLOG("SETUP", "Confirmed enabled");
		}
		else
		{
			MYLOG("SETUP", "Confirmed disabled");
		}

		MYLOG("SETUP", "Retry = %d", g_confirmed_retry);

		MYLOG("SETUP", "DR = %d", g_data_rate);
	}

	// To be checked if this makes sense
	// api.lorawan.join();

	// Needs some strategy when to switch off the power for the modules
	// digitalWrite(WB_IO2, LOW);
}

/**
 * @brief sensor_handler is a timer function called every
 * g_send_repeat_time milliseconds. Default is 120000. Can be
 * changed in main.h
 *
 */
void sensor_handler(void *)
{
	MYLOG("UPLINK", "Start");
	digitalWrite(LED_BLUE, HIGH);

	if (api.lorawan.nwm.get() == 1)
	{ // Check if the node has joined the network
		if (!api.lorawan.njs.get())
		{
			MYLOG("UPLINK", "Not joined, skip sending");
			return;
		}
	}

	// Clear payload
	g_solution_data.reset();

/**************************************/
/**************************************/
/** Insert here sensor specific codes */
/**************************************/
/**************************************/
#include "sensor_handler.h"

	// Add battery voltage
	g_solution_data.addVoltage(LPP_CHANNEL_BATT, api.system.bat.get());

	// Read sensor data
	get_sensor_values();

	// Send the packet
	send_packet();
}

/**
 * @brief This example is complete timer
 * driven. The loop() does nothing than
 * sleep.
 *
 */
void loop()
{
	api.system.sleep.all();
	// api.system.scheduler.task.destroy();
}

/**
 * @brief Send the data packet that was prepared in
 * Cayenne LPP format by the different sensor and location
 * aqcuision functions
 *
 */
void send_packet(void)
{
	if (api.lorawan.nwm.get() == 1)
	{
		uint8_t proposed_dr = get_min_dr(api.lorawan.band.get(), g_solution_data.getSize());
		MYLOG("UPLINK", "Check if datarate allows payload size, proposed is DR %d, current DR is %d", proposed_dr, api.lorawan.dr.get());

		if (proposed_dr == 16)
		{
			MYLOG("UPLINK", "No matching DR found");
		}
		else
		{
			if (proposed_dr < api.lorawan.dr.get())
			{
				if (auto_dr_enabled)
				{
					MYLOG("UPLINK", "Proposed DR is lower than current selected, if enabled, switching to lower DR");
					api.lorawan.dr.set(proposed_dr);
				}
			}

			if (proposed_dr > api.lorawan.dr.get())
			{
				if (auto_dr_enabled)
				{
					MYLOG("UPLINK", "Proposed DR is higher than current selected, if enabled, switching to higher DR");
					api.lorawan.dr.set(proposed_dr);
				}
			}
		}

		// Send the packet
		if (api.lorawan.send(g_solution_data.getSize(), g_solution_data.getBuffer(), set_fPort, g_confirmed_mode, g_confirmed_retry))
		{
			MYLOG("UPLINK", "Packet enqueued, size %d", g_solution_data.getSize());
			tx_active = true;
		}
		else
		{
			MYLOG("UPLINK", "Send failed");
		}
	}
	else
	{
		MYLOG("UPLINK", "Send packet with size %d over P2P", g_solution_data.getSize() + 8);

		digitalWrite(LED_BLUE, LOW);
		uint8_t packet_buffer[g_solution_data.getSize() + 8];
		if (!api.lorawan.deui.get(packet_buffer, 8))
		{
			MYLOG("UPLINK", "Could not get DevEUI");
		}

		memcpy(&packet_buffer[8], g_solution_data.getBuffer(), g_solution_data.getSize());

		for (int idx = 0; idx < g_solution_data.getSize() + 8; idx++)
		{
			Serial.printf("%02X", packet_buffer[idx]);
		}
		Serial.println("");

		if (api.lorawan.psend(g_solution_data.getSize() + 8, packet_buffer))
		{
			MYLOG("UPLINK", "Packet enqueued");
		}
		else
		{
			MYLOG("UPLINK", "Send failed");
		}
	}
}
