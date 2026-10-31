from ngan_hang_data import DANH_SACH_NGAN_HANG # nhd

def chuan_hoa_va_check_ngan_hang(t): # chvccn
    k = t.strip().lower()
    if k in DANH_SACH_NGAN_HANG:
        return True, DANH_SACH_NGAN_HANG[k]
    for x, y in DANH_SACH_NGAN_HANG.items():
        if x in k or k in x:
            return True, y
    return False, ""
