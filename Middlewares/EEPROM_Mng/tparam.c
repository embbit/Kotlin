/***************************************************************************************************
 *   Project:       
 *   Author:        Alex Borisov
 ***************************************************************************************************
 *   Distribution:  Copyright � 2008 Alex Borisov
 *
 ***************************************************************************************************
 *   MCU Family:    ---
 *   Compiler:      ---
 ***************************************************************************************************
 *   File:          tparam.c
 *   Description:   ���������� ����������
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
 * ������ ����� ��������� � ����������������� ������.
 * 
 * @param val    ��������� �� �������� ���������
 * @param tbl    ��������� �� ������� ������������
 * @param i      ������ ��������� � ������� ������������
 * @param cp     ����� ����� �� 0 �� 2
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
 * ���������� ����� ��������� �� ����������������� ������ �� ���������� ����� imbuf 
 *  
 * @param tbl    ��������� �� ������� ������������
 * @param i      ������ ��������� � ������� ������������
 * @param cp     ����� ����� �� 0 �� 2
 * 
 * @return bool  true, ���� �������� ������ ������� (�������� �������� CRC)
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
 * ������ ����� ��������� � ����������������� ������ � ����������� ������������ 
 * 
 * @param tbl      ��������� �� ������� ������������
 * @param indx     ������ ��������� � ������� ������������
 * @param cp       ����� ����� �� 0 �� 2
 * 
 * @return bool    true, ���� �������� ������� ������� (����������� ��������)
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
 * ��������� ������� ��������� � ������� ������������ �� ��������� �� ������� ����� � ��� 
 * 
 * @param val      ��������� �� ������� ����� ��������� � ���
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
 * ������������� (����������) ���� ���������� �� ������� tbl. ��������! ������� �� ����������
 * ������� ��������� � ���, ��� �� �������� ������ �������, ��� ��� �������� ������������ ��
 * �������� �� ���������
 * 
 * @param TPARAM_TBL    ��������� �� ������� ������������
 * @return              TPARAM_ERR_NO - �������� ���������� 
 *                      TPARAM_ERR_WPARAM - ������ �������� ���������� � �������
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
 * �������� ������� ����� ��������� �� ������� � ����������������� ������
 *  
 * @param tbl       ��������� �� ������� ������������
 * @param indx      ������ ��������� � �������
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
        /* ������ �������� ��� CRC */
        case TPARAM_SAFETY_LEVEL_0:
            tparam_nv_read(addr, size, imbuf);           
            memcpy(val, imbuf, size);           
            break;

        /* ���� ������ � CRC */
        case TPARAM_SAFETY_LEVEL_1:

            tparam_lock();
            if (tparam_read_wcrc(tbl, i, 0)) {
                memcpy(val, imbuf, size);
            }
            else
            {
                /* ��������������� �������� �� default */
                memcpy(val, def, size);
                ret = tparam_write_verify(def, tbl, i, 0) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
            }
            break;

        /* ��� ������ � CRC */
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
                    /* ��������� �� �����, ��������� 2 ��������� �� 1 */
                    ret = (tparam_write_verify(val, tbl, i, 1)) ? TPARAM_ERR_RESTORE : TPARAM_ERR_WRITE;
                }
            }
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* ��� ������ � CRC */

            break;
        default:
            break;
    }
    tparam_unlock(); 
    return ret;
}


/**
 * ���������� �������� �������� ��������� � ����������������� ������
 * 
 * @param TPARAM_TBL   ��������� �� ������� ������������
 * @param i            ������ ��������� � �������
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
        /* ������ �������� ��� CRC */
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

        /* ���� ������ � CRC */
        case TPARAM_SAFETY_LEVEL_1:
            if (tparam_write_verify(val, tbl, i, 0))
                ret = TPARAM_ERR_NO;
            break;

        /* ��� ������ � CRC */
        case TPARAM_SAFETY_LEVEL_2:
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1)
               )
                ret = TPARAM_ERR_NO;
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* ��� ������ � CRC */
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
 * �������� ������� ����� ��������� �� ������� � ����������������� ������
 * 
 * @param tbl   ��������� �� ������� ������������ 
 * @param val   ��������� �� ������� ����� ��������� � ���
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
 * ���������� �������� �������� ��������� � ����������������� ������ 
 * 
 * @param tbl   ��������� �� ������� ������������ 
 * @param val   ��������� �� ������� ����� ��������� � ���
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
 * ����� ��������� �� �������� �� ���������
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
        /* ������ �������� ��� CRC */
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

        /* ���� ������ � CRC */
        case TPARAM_SAFETY_LEVEL_1:
            if (tparam_write_verify(val, tbl, i, 0))
                ret = TPARAM_ERR_NO;
            break;

        /* ��� ������ � CRC */
        case TPARAM_SAFETY_LEVEL_2:
            if (tparam_write_verify(val, tbl, i, 0) &&
                tparam_write_verify(val, tbl, i, 1)
               )
                ret = TPARAM_ERR_NO;
            break;

        case TPARAM_SAFETY_LEVEL_3:
            /* ��� ������ � CRC */
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
 * ����� ��������� �� �������� �� ���������
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


