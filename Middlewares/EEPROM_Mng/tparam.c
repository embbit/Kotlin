/***************************************************************************************************
 *   Project:       
 *   Author:        Alex Borisov
 ***************************************************************************************************
 *   Distribution:  Copyright © 2008 Alex Borisov
 *
 ***************************************************************************************************
 *   MCU Family:    ---
 *   Compiler:      ---
 ***************************************************************************************************
 *   File:          tparam.c
 *   Description:   Библиотека параметров
 *
 ***************************************************************************************************
 *   History:       14.09.2010 - [Alex Borisov] - file created
 *
 **************************************************************************************************/

/***************************************************************************************************
 *                                         INCLUDED FILES
 **************************************************************************************************/

#include <string.h>
#include "tparam.h"

/***************************************************************************************************
 *                                           DEFINITIONS
 **************************************************************************************************/

#define IMBUF_CPY(cp, size)       imbuf + ((cp) * ((size) + TPARAM_CRC_SIZE))

/***************************************************************************************************
 *                                           PRIVATE DATA
 **************************************************************************************************/

static U08 imbuf[TPARAM_BUF_SIZE];

/***************************************************************************************************
 *                                        PRIVATE FUNCTIONS
 **************************************************************************************************/

/**
 * Запись копии параметра в энергонезависимую память.
 * 
 * @param val    указатель на значение параметра
 * @param tbl    указатель на таблицу дескрипторов
 * @param i      индекс параметра в таблице дескрипторов
 * @param cp     номер копии от 0 до 2
 */
static void tparam_write_wcrc (void const *val, TPARAM_TBL const *tbl, U16_FAST i, U08_FAST cp) 
{
    TPARAM_DESC const *dt  = tbl->dt;
    TPARAM_ADDR size       = dt[i].size;
    U32         addr       = tbl->addr + dt[i].addr;
    TPARAM_ADDR shift      = cp * (size + TPARAM_CRC_SIZE);
    TPARAM_CRC  crc;

    memcpy(imbuf + shift, val, size);
    crc = tparam_crc(imbuf + shift, size);
    memcpy(imbuf + shift + size, &crc, TPARAM_CRC_SIZE);
    tparam_nv_write(addr + shift, size + TPARAM_CRC_SIZE, imbuf);

}

/**
 * Считывание копии параметра из энергонезависимой памяти во внутренний буфер imbuf 
 *  
 * @param tbl    указатель на таблицу дескрипторов
 * @param i      индекс параметра в таблице дескрипторов
 * @param cp     номер копии от 0 до 2
 * 
 * @return bool  true, если параметр считан успешно (пройдена проверка CRC)
 */
static bool tparam_read_wcrc (TPARAM_TBL const *tbl, U16_FAST i, U08_FAST cp)
{
    TPARAM_DESC const *dt  = tbl->dt;
    TPARAM_ADDR size       = dt[i].size;
    U32         addr       = tbl->addr + dt[i].addr;
    TPARAM_ADDR shift      = cp * (size + TPARAM_CRC_SIZE);
    TPARAM_CRC  crc;
    
    tparam_nv_read(addr + shift, size + TPARAM_CRC_SIZE, imbuf + shift);
    crc = tparam_crc(imbuf + shift, size);
    if (memcmp(&crc, imbuf + shift + size, TPARAM_CRC_SIZE) == 0)
        return true;
    return false;
}

/**
 * Запись копии параметра в энергонезависимую память с последующей верификацией 
 * 
 * @param tbl      указатель на таблицу дескрипторов
 * @param indx     индекс параметра в таблице дескрипторов
 * @param cp       номер копии от 0 до 2
 * 
 * @return bool    true, если параметр записан успешно (верификация пройдена)
 */
static bool tparam_write_verify (void const *val, TPARAM_TBL const *tbl, U16_FAST indx, U08_FAST cp)
{
    U08_FAST i;
    bool ret = false;
    for (i = 0; i < TPARAM_TRY_NUM; i++)
    {
        tparam_write_wcrc(val, tbl, indx, cp);
        if (tparam_read_wcrc(tbl, indx, cp))
        {
            ret = true;    
            break;
        }
    }
    return ret;
}


/**
 * Получение индекса параметра в таблице дескрипторов по указателю на рабочую копию в ОЗУ 
 * 
 * @param val      указатель на рабочую копию параметра в ОЗУ
 * 
 * @return TPARAM_ADDR 
 */
static U16_FAST tparam_indx_get (TPARAM_TBL const *tbl, void *val)
{
    U16_FAST i;
    TPARAM_DESC const *dt;

    if (tbl == NULL)
        return UINT_FAST16_MAX;

    dt = tbl->dt;
    for (i = 0; i < tbl->pnum; i++)
    {
        if (dt[i].val == val)
            return i;
    }
    return UINT_FAST16_MAX;
}

/***************************************************************************************************
 *                                         PUBLIC FUNCTIONS
 **************************************************************************************************/

/**
 * Инициализация (считывание) всех параметров из таблицы tbl. Внимание! Функция не возвращает
 * никаких сообщений о том, был ли параметр считан успешно, или его пришлось восстановить из
 * значения по умолчанию
 * 
 * @param TPARAM_TBL    указатель на таблицу дескрипторов
 * @return              TPARAM_ERR_NO - успешное выполнение 
 *                      TPARAM_ERR_WPARAM - ошибка передачи параметров в функцию
 */
TPARAM_ERR tparam_init (TPARAM_TBL const *tbl)
{
    U16_FAST i;

    if (tbl == NULL)
        return TPARAM_ERR_WPARAM;

    for (i = 0; i < tbl->pnum; i++) {
        tparam_load(tbl, i);
    }
    return TPARAM_ERR_NO;
}


/**
 * Загрузка рабочей копии параметра из таблицы в энергонезависимой памяти
 *  
 * @param tbl       указатель на таблицу дескрипторов
 * @param indx      индекс параметра в таблице
 */
TPARAM_ERR tparam_load (TPARAM_TBL const *tbl, U16_FAST i)
{
    bool r1, r2;
    //bool r3;

    TPARAM_ERR ret = TPARAM_ERR_NO;
    TPARAM_DESC const *dt;
    TPARAM_ADDR size;
    U32         addr;
    void *val;
    void const *def;

    if (tbl == NULL)
        return TPARAM_ERR_WPARAM;

    dt   = tbl->dt;
    size = dt[i].size;
    addr = tbl->addr + dt[i].addr;
    val  = dt[i].val;
    def  = dt[i].def;

    tparam_lock(); 
    switch (dt[i].attr & TPARAM_SAFETY_LEVEL_MASK)
    {
        /* просто значение без CRC */
        case TPARAM_SAFETY_LEVEL_0:
            tparam_nv_read(addr, size, imbuf);           
            memcpy(val, imbuf, size);           
            break;

        /* одна запись с CRC */
        case TPARAM_SAFETY_LEVEL_1:

            tparam_lock();
            if (tparam_read_wcrc(tbl, i, 0)) {
                memcpy(val, imbuf, size);
            }
            else
            {
                /* восстанавливаем параметр из default */
                memcpy(val, def, size);
                ret = tparam_write_verify(def, tbl, i, 0) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
            }
            break;

        /* две записи с CRC */
        case TPARAM_SAFETY_LEVEL_2:

            r1 = tparam_read_wcrc(tbl, i, 0);
            r2 = tparam_read_wcrc(tbl, i, 1);
            
            if (r1 == false && r2 == false)
            {
                memcpy(val, def, size);
                ret =  (tparam_write_verify(def, tbl, i, 0) &&
                        tparam_write_verify(def, tbl, i, 1)) ?
                    TPARAM_ERR_RESTORE :
                    TPARAM_ERR_WRITE;
            }
            else if (r1 == true && r2 == false)
            {
                memcpy(val, IMBUF_CPY(0, size), size);
                ret = (tparam_write_verify(val, tbl, i, 1)) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
            }
            else if (r1 == false && r2 == true)
            {
                memcpy(val, IMBUF_CPY(1, size), size);
                ret = (tparam_write_verify(val, tbl, i, 0)) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
            }
            else if (r1 == true &&  r2 == true)
            {
                memcpy(val, IMBUF_CPY(0, size), size);
                if (memcmp(IMBUF_CPY(0, size), IMBUF_CPY(1, size), size))
                {
                    /* параметры не равны, обновляем 2 значением из 1 */
                    ret = (tparam_write_verify(val, tbl, i, 1)) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
                }
            }
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* три записи с CRC */

            break;
        default:
            break;
    }
    tparam_unlock(); 
    return ret;
}


/**
 * Сохранение текущего значения параметра в энергонезависимой памяти
 * 
 * @param TPARAM_TBL   указатель на таблицу дескрипторов
 * @param i            индекс параметра в таблице
 * @return
 */
TPARAM_ERR tparam_save (TPARAM_TBL const *tbl, U16_FAST i)
{
    TPARAM_ERR ret = TPARAM_ERR_WRITE;

    TPARAM_DESC const *dt;
    TPARAM_ADDR size;
    TPARAM_ADDR addr;
    void *val;

    if (tbl == NULL)
        return TPARAM_ERR_WPARAM;

    dt   = tbl->dt;
    size = dt[i].size;
    addr = dt[i].addr;
    val  = dt[i].val;

    tparam_lock();
    switch (dt[i].attr & TPARAM_SAFETY_LEVEL_MASK)
    {
        /* просто значение без CRC */
        case TPARAM_SAFETY_LEVEL_0:
            for (i = 0; i < TPARAM_TRY_NUM; i++)
            {
                memcpy(imbuf, val, size);
                tparam_nv_write(addr, size, imbuf);
                tparam_nv_read (addr, size, imbuf);
                if (memcmp(imbuf, val, size) == 0)
                    ret = TPARAM_ERR_NO;
            }
            break;

        /* одна запись с CRC */
        case TPARAM_SAFETY_LEVEL_1:
            if (tparam_write_verify(val, tbl, i, 0))
                ret = TPARAM_ERR_NO;
            break;

        /* две записи с CRC */
        case TPARAM_SAFETY_LEVEL_2:
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1)
               )
                ret = TPARAM_ERR_NO;
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* три записи с CRC */
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1) &&
                tparam_write_verify(val, tbl, i, 2)
               )
                ret = TPARAM_ERR_NO;
            break;

        default:
            break;
    }
    tparam_unlock();

    return ret;
}




/**
 * Загрузка рабочей копии параметра из таблицы в энергонезависимой памяти
 * 
 * @param tbl   указатель на таблицу дескрипторов 
 * @param val   указатель на рабочую копию параметра в ОЗУ
 * 
 * @return TPARAM_ERR 
 */
TPARAM_ERR tparam_load_p (TPARAM_TBL const *tbl, void *val)
{
    U16_FAST i;

    if ((i = tparam_indx_get(tbl, val)) == UINT_FAST16_MAX)
        return TPARAM_ERR_WPARAM;
    return tparam_load(tbl, i);
}

/**
 * Сохранение текущего значения параметра в энергонезависимой памяти 
 * 
 * @param tbl   указатель на таблицу дескрипторов 
 * @param val   указатель на рабочую копию параметра в ОЗУ
 * 
 * @return TPARAM_ERR 
 */
TPARAM_ERR tparam_save_p (TPARAM_TBL const *tbl, void *val)
{
    U16_FAST i;

    if ((i = tparam_indx_get(tbl, val)) == UINT_FAST16_MAX)
        return TPARAM_ERR_WPARAM;
    return tparam_save(tbl, i);
}


/**
 * Сброс параметра на значение по умолчанию
 *
 * @param tbl 
 * @param i 
 * 
 * @return TPARAM_ERR 
 */
TPARAM_ERR tparam_reset (TPARAM_TBL const *tbl, U16_FAST i)
{
    TPARAM_ERR ret = TPARAM_ERR_WRITE;

    TPARAM_DESC const *dt;
    TPARAM_ADDR size;
    TPARAM_ADDR addr;
    void const *val;

    if (tbl == NULL)
        return TPARAM_ERR_WPARAM;

    dt   = tbl->dt;
    size = dt[i].size;
    addr = dt[i].addr;
    val  = dt[i].def;

    tparam_lock();
    switch (dt[i].attr & TPARAM_SAFETY_LEVEL_MASK)
    {
        /* просто значение без CRC */
        case TPARAM_SAFETY_LEVEL_0:
            for (i = 0; i < TPARAM_TRY_NUM; i++)
            {
                memcpy(imbuf, val, size);
                tparam_nv_write(addr, size, imbuf);
                tparam_nv_read (addr, size, imbuf);
                if (memcmp(imbuf, val, size) == 0)
                    ret = TPARAM_ERR_NO;
            }
            break;

        /* одна запись с CRC */
        case TPARAM_SAFETY_LEVEL_1:
            if (tparam_write_verify(val, tbl, i, 0))
                ret = TPARAM_ERR_NO;
            break;

        /* две записи с CRC */
        case TPARAM_SAFETY_LEVEL_2:
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1)
               )
                ret = TPARAM_ERR_NO;
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* три записи с CRC */
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1) &&
                tparam_write_verify(val, tbl, i, 2)
               )
                ret = TPARAM_ERR_NO;
            break;

        default:
            break;
    }
    tparam_unlock();

    return ret;
}


/**
 * Сброс параметра на значение по умолчанию
 *
 * @param tbl 
 * @param val 
 * 
 * @return TPARAM_ERR 
 */
TPARAM_ERR tparam_reset_p (TPARAM_TBL const *tbl, void *val)
{
    U16_FAST i;

    if ((i = tparam_indx_get(tbl, val)) == UINT_FAST16_MAX)
        return TPARAM_ERR_WPARAM;
    return tparam_reset(tbl, i);    
}


/***************************************************************************************************
 *  end of file: tparam.c
 **************************************************************************************************/


