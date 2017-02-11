/**
  ******************************************************************************
  * File Name          : freertos.c
  * Description        : Code for freertos applications
  ******************************************************************************
  *
  * Copyright (c) 2017 STMicroelectronics International N.V. 
  * All rights reserved.
  *
  * Redistribution and use in source and binary forms, with or without 
  * modification, are permitted, provided that the following conditions are met:
  *
  * 1. Redistribution of source code must retain the above copyright notice, 
  *    this list of conditions and the following disclaimer.
  * 2. Redistributions in binary form must reproduce the above copyright notice,
  *    this list of conditions and the following disclaimer in the documentation
  *    and/or other materials provided with the distribution.
  * 3. Neither the name of STMicroelectronics nor the names of other 
  *    contributors to this software may be used to endorse or promote products 
  *    derived from this software without specific written permission.
  * 4. This software, including modifications and/or derivative works of this 
  *    software, must execute solely and exclusively on microcontroller or
  *    microprocessor devices manufactured by or for STMicroelectronics.
  * 5. Redistribution and use of this software other than as permitted under 
  *    this license is void and will automatically terminate your rights under 
  *    this license. 
  *
  * THIS SOFTWARE IS PROVIDED BY STMICROELECTRONICS AND CONTRIBUTORS "AS IS" 
  * AND ANY EXPRESS, IMPLIED OR STATUTORY WARRANTIES, INCLUDING, BUT NOT 
  * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
  * PARTICULAR PURPOSE AND NON-INFRINGEMENT OF THIRD PARTY INTELLECTUAL PROPERTY
  * RIGHTS ARE DISCLAIMED TO THE FULLEST EXTENT PERMITTED BY LAW. IN NO EVENT 
  * SHALL STMICROELECTRONICS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
  * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
  * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, 
  * OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF 
  * LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING 
  * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
  * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
  *
  ******************************************************************************
  */

/* Includes ------------------------------------------------------------------*/
#include "FreeRTOS.h"
#include "task.h"
#include "cmsis_os.h"

/* USER CODE BEGIN Includes */     
#include "vscp_core.h"
#include "vscp_timer.h"
#include "main.h"
#include "gpio.h"
/* USER CODE END Includes */

/* Variables -----------------------------------------------------------------*/
osThreadId defaultTaskHandle;
osThreadId VSCP_coreHandle;
osThreadId VSCP_timerHandle;
osThreadId VSCP_LEDHandle;
osMessageQId queueVSCP_LED_taskHandle;

/* USER CODE BEGIN Variables */

/* USER CODE END Variables */

/* Function prototypes -------------------------------------------------------*/
void StartDefaultTask(void const * argument);
void taskVSCP_core_process(void const * argument);
void taskVSCP_timer_process(void const * argument);
void taskVSCP_LED_worker(void const * argument);

void MX_FREERTOS_Init(void); /* (MISRA C 2004 rule 8.1) */

/* USER CODE BEGIN FunctionPrototypes */

/* USER CODE END FunctionPrototypes */

/* Hook prototypes */

/* Init FreeRTOS */

void MX_FREERTOS_Init(void) {
  /* USER CODE BEGIN Init */
       
  /* USER CODE END Init */

  /* USER CODE BEGIN RTOS_MUTEX */
  /* add mutexes, ... */
  /* USER CODE END RTOS_MUTEX */

  /* USER CODE BEGIN RTOS_SEMAPHORES */
  /* add semaphores, ... */
  /* USER CODE END RTOS_SEMAPHORES */

  /* USER CODE BEGIN RTOS_TIMERS */
  /* start timers, add new ones, ... */
  /* USER CODE END RTOS_TIMERS */

  /* Create the thread(s) */
  /* definition and creation of defaultTask */
  osThreadDef(defaultTask, StartDefaultTask, osPriorityNormal, 0, 128);
  defaultTaskHandle = osThreadCreate(osThread(defaultTask), NULL);

  /* definition and creation of VSCP_core */
  osThreadDef(VSCP_core, taskVSCP_core_process, osPriorityNormal, 0, 128);
  VSCP_coreHandle = osThreadCreate(osThread(VSCP_core), NULL);

  /* definition and creation of VSCP_timer */
  osThreadDef(VSCP_timer, taskVSCP_timer_process, osPriorityNormal, 0, 128);
  VSCP_timerHandle = osThreadCreate(osThread(VSCP_timer), NULL);

  /* definition and creation of VSCP_LED */
  osThreadDef(VSCP_LED, taskVSCP_LED_worker, osPriorityBelowNormal, 0, 128);
  VSCP_LEDHandle = osThreadCreate(osThread(VSCP_LED), NULL);

  /* USER CODE BEGIN RTOS_THREADS */
  /* add threads, ... */
  /* USER CODE END RTOS_THREADS */

  /* Create the queue(s) */
  /* definition and creation of queueVSCP_LED_task */
  osMessageQDef(queueVSCP_LED_task, 4, VSCP_LAMP_STATE);
  queueVSCP_LED_taskHandle = osMessageCreate(osMessageQ(queueVSCP_LED_task), NULL);

  /* USER CODE BEGIN RTOS_QUEUES */
  /* add queues, ... */
  /* USER CODE END RTOS_QUEUES */
}

/* StartDefaultTask function */
void StartDefaultTask(void const * argument)
{

  /* USER CODE BEGIN StartDefaultTask */
  /* Infinite loop */
  for(;;)
  {
    osDelay(1);
  }
  /* USER CODE END StartDefaultTask */
}

/* taskVSCP_core_process function */
void taskVSCP_core_process(void const * argument)
{
  /* USER CODE BEGIN taskVSCP_core_process */
  TickType_t xLastWakeTime;
  volatile uint8_t VSCP_Button_pressed = 0;  
    
  vscp_core_init();
  xLastWakeTime = xTaskGetTickCount();
  /* Infinite loop */
  for(;;)
  {
    osDelayUntil(&xLastWakeTime, VSCP_CORE_PERIOD/portTICK_PERIOD_MS);
    xLastWakeTime = xTaskGetTickCount();
    vscp_core_process();
    if (VSCP_Button_pressed)
    {
        vscp_core_startNodeSegmentInit();
        VSCP_Button_pressed = 0;
    }

  }
  /* USER CODE END taskVSCP_core_process */
}

/* taskVSCP_timer_process function */
void taskVSCP_timer_process(void const * argument)
{
  /* USER CODE BEGIN taskVSCP_timer_process */
  TickType_t xLastWakeTime;
  xLastWakeTime = xTaskGetTickCount();    
  /* Infinite loop */
  for(;;)
  {
    osDelayUntil(&xLastWakeTime, (VSCP_TIMER_PERIOD/portTICK_PERIOD_MS));
    xLastWakeTime = xTaskGetTickCount();
    vscp_timer_process(VSCP_TIMER_PERIOD);
  }
  /* USER CODE END taskVSCP_timer_process */
}

/* taskVSCP_LED_worker function */
void taskVSCP_LED_worker(void const * argument)
{
  /* USER CODE BEGIN taskVSCP_LED_worker */
  VSCP_LAMP_STATE state;
  TickType_t Period = portMAX_DELAY ;   
    
  /* Infinite loop */
  for(;;)
  {
         xQueueReceive( queueVSCP_LED_taskHandle, &( state ), Period );
         switch (state)
         {
             case VSCP_LAMP_STATE_ON:
                 Period = portMAX_DELAY;
                 HAL_GPIO_WritePin(VSCP_LED_GPIO_Port, VSCP_LED_Pin, GPIO_PIN_RESET);
                 break;
             case VSCP_LAMP_STATE_OFF:
                 Period = portMAX_DELAY;
                 HAL_GPIO_WritePin(VSCP_LED_GPIO_Port, VSCP_LED_Pin, GPIO_PIN_SET);
                 break;
             case VSCP_LAMP_STATE_BLINK_FAST:
                 Period = VSCP_LED_PERIOD_FAST / portTICK_PERIOD_MS;
                 HAL_GPIO_TogglePin(VSCP_LED_GPIO_Port, VSCP_LED_Pin);
                 break;
             case VSCP_LAMP_STATE_BLINK_SLOW:
                 Period = VSCP_LED_PERIOD_SLOW / portTICK_PERIOD_MS;
                 HAL_GPIO_TogglePin(VSCP_LED_GPIO_Port, VSCP_LED_Pin);
                 break;
             default:
                 break;
       }
  }
  /* USER CODE END taskVSCP_LED_worker */
}

/* USER CODE BEGIN Application */
     
/* USER CODE END Application */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
