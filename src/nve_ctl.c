#include <errno.h>
#include <ctype.h>
#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

struct nve_info {
    uint32_t operation;
    uint32_t number;
    char name[8];
    uint32_t size;
    unsigned char data[104];
};
_Static_assert(sizeof(struct nve_info) == 124, "NVE ABI size");
#define NVE_IOCTL _IOWR('M', 25, struct nve_info)

static int hex32(const char *s, unsigned char out[32]) {
    if (strlen(s) != 64) return -1;
    for (int i = 0; i < 32; i++) {
        unsigned x;
        if (!isxdigit((unsigned char)s[2*i]) || !isxdigit((unsigned char)s[2*i+1])) return -1;
        if (sscanf(s + 2*i, "%2x", &x) != 1) return -1;
        out[i] = x;
    }
    return 0;
}

static int read_key(int fd, unsigned char out[32]) {
    struct nve_info n = {.operation = 1, .number = 315, .name = "USRKEY", .size = 32};
    if (ioctl(fd, NVE_IOCTL, &n) < 0) return -1;
    if (n.number != 315 || memcmp(n.name, "USRKEY", 6) || n.size != 32) {
        errno = EPROTO;
        return -1;
    }
    memcpy(out, n.data, 32);
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2 && argc != 4) {
        fprintf(stderr, "usage: %s read | write EXPECTED_SHA256 NEW_SHA256\n", argv[0]);
        return 2;
    }
    int fd = open("/dev/nve0", O_RDWR | O_CLOEXEC);
    if (fd < 0) { perror("open nve0"); return 1; }
    unsigned char before[32], expected[32], desired[32], after[32];
    if (read_key(fd, before) < 0) { perror("read USRKEY"); close(fd); return 1; }
    if (argc == 2 && strcmp(argv[1], "read") == 0) {
        for (int i = 0; i < 32; i++) printf("%02x", before[i]);
        puts("");
        close(fd);
        return 0;
    }
    if (argc != 4 || strcmp(argv[1], "write") || hex32(argv[2], expected) || hex32(argv[3], desired)) {
        fputs("invalid arguments\n", stderr); close(fd); return 2;
    }
    if (memcmp(before, expected, 32)) {
        fputs("USRKEY changed since backup; write aborted\n", stderr); close(fd); return 1;
    }
    struct nve_info n = {.operation = 0, .number = 315, .name = "USRKEY", .size = 32};
    memcpy(n.data, desired, 32);
    if (ioctl(fd, NVE_IOCTL, &n) < 0) { perror("write USRKEY"); close(fd); return 1; }
    if (read_key(fd, after) < 0 || memcmp(after, desired, 32)) {
        fputs("USRKEY read-back mismatch\n", stderr); close(fd); return 1;
    }
    puts("USRKEY write and read-back verified");
    close(fd);
    return 0;
}
