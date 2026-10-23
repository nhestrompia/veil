#include <stdint.h>

int32_t AFBOpenHIDPosting(uint32_t *connection);
void AFBCloseHIDPosting(uint32_t connection);
int32_t AFBPostHIDKey(uint32_t connection, uint16_t keyCode, uint16_t character,
                      int down, int managerReports);
