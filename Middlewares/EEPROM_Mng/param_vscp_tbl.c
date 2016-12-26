/* Parameterrs table */


#include "param_vscp_list.h"	// parameters list

const TPARAM_DESC param_vscp_desc_table[] = 
{
/* (  0) */ { 0x0, TPARAM_SAFETY_LEVEL_0,   1, &vscp_boot_flag,       &vscp_boot_flag_def}, // Boot flag (jump to application or stay in bootloader)
/* (  1) */ { 0x1, TPARAM_SAFETY_LEVEL_0,   1, &vscp_nickname_id,     &vscp_nickname_id_def}, // VSCP nickname id
/* (  2) */ { 0x2, TPARAM_SAFETY_LEVEL_1,   1, &vscp_segment_controller_crc, &vscp_segment_controller_crc_def}, // Segment controller CRC
/* (  3) */ { 0x4, TPARAM_SAFETY_LEVEL_1,   1, &vscp_node_control_flags, &vscp_node_control_flags_def}, // Node control flags
/* (  4) */ { 0x6, TPARAM_SAFETY_LEVEL_1,   5, &vscp_user_id,         &vscp_user_id_def}, // User id 
/* (  5) */ { 0xC, TPARAM_SAFETY_LEVEL_1,  16, &vscp_node_guid,       &vscp_node_guid_def}, // GUID
/* (  6) */ { 0x1D, TPARAM_SAFETY_LEVEL_1,   1, &vscp_node_zone,       &vscp_node_zone_def}, // Node zone
/* (  7) */ { 0x1F, TPARAM_SAFETY_LEVEL_1,   1, &vscp_node_subzone,    &vscp_node_subzone_def}, // Node sub zone
/* (  8) */ { 0x21, TPARAM_SAFETY_LEVEL_1,   4, &vscp_mfg_device_id,   &vscp_mfg_device_id_def}, // Manufacturer device id
/* (  9) */ { 0x26, TPARAM_SAFETY_LEVEL_1,   4, &vscp_mfg_device_sub_id, &vscp_mfg_device_sub_id_def}, // Manufacturer sub device id
/* ( 10) */ { 0x2B, TPARAM_SAFETY_LEVEL_1,  32, &vscp_mdf_url,         &vscp_mdf_url_def}, // MDF URL
/* ( 11) */ { 0x4C, TPARAM_SAFETY_LEVEL_1,   4, &vscp_device_family_code, &vscp_device_family_code_def}, // Family code
/* ( 12) */ { 0x51, TPARAM_SAFETY_LEVEL_1,   4, &vscp_device_type,     &vscp_device_type_def}, // Device type
/* ( 13) */ { 0x56, TPARAM_SAFETY_LEVEL_1,   1, &vscp_log_id,          &vscp_log_id_def}, // Log id (stream)
/* ( 14) */ { 0x58, TPARAM_SAFETY_LEVEL_1,   1, &vscp_std_dm_rows,     &vscp_std_dm_rows_def}, // Standard decision matrix
/* ( 15) */ { 0x5A, TPARAM_SAFETY_LEVEL_1,   1, &vscp_std_dm_rows_size, &vscp_std_dm_rows_size_def}, // Decision matrix (standard or extension) row size in bytes
/* ( 16) */ { 0x5C, TPARAM_SAFETY_LEVEL_1,  80, &vscp_std_dm,          &vscp_std_dm_def}, // Decision matrix next generation
};

const TPARAM_TBL param_vscp_table = {
    0x0, // absolute table addres in NVRAM (U32)
    173, // table size in NVRAM (bytes)
    17, // number of parametes in table
    param_vscp_desc_table
};

