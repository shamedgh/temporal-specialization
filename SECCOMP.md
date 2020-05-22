# Install SECCOMP BPF filters in application (manual)

After the list of filtered system calls is generated we have to install
seccomp filters to prevent their execution by modifying the source code of the
application. This has to be done by modifying the function/s which are run to
start the serving phase. The name of the function is specified in the
app.to.properties.json file. You must find the place where these functions are
defined and install the seccomp filters there.

To install a seccomp filter apply the following changes to the application
source code.

1. Add seccomp header to c code which requires the filter installation code.
```
#include <linux/seccomp.h>
```

2. Define the following functions to install filters.
```
static int install_filter(int nr, int arch, int error) {
  struct sock_filter filter[] = {
      BPF_STMT(BPF_LD + BPF_W + BPF_ABS, (offsetof(struct seccomp_data, arch))),
      BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, arch, 0, 3),
      BPF_STMT(BPF_LD + BPF_W + BPF_ABS, (offsetof(struct seccomp_data, nr))),
      BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, nr, 0, 1),
      BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ERRNO | (error & SECCOMP_RET_DATA)),
      BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ALLOW),
  };
  struct sock_fprog prog = {
      .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
      .filter = filter,
  };
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) {
    return 1;
  }
  if (prctl(PR_SET_SECCOMP, 2, &prog)) {
    return 1;
  }
  return 0;
}

static int revoke_seccomp_manipulation(int error) {
    int nr = __NR_prctl;
    int arch = AUDIT_ARCH_X86_64;
  struct sock_filter filter[] = {
      BPF_STMT(BPF_LD + BPF_W + BPF_ABS, (offsetof(struct seccomp_data, arch))),
      BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, arch, 0, 5),
      BPF_STMT(BPF_LD + BPF_W + BPF_ABS, (offsetof(struct seccomp_data, nr))),
      BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, nr, 0, 3),
      BPF_STMT(BPF_LD + BPF_W + BPF_ABS, (offsetof(struct seccomp_data, args[0]))),
      BPF_JUMP(BPF_JMP + BPF_JEQ + BPF_K, PR_SET_SECCOMP, 0, 1),
      BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ERRNO | (error & SECCOMP_RET_DATA)),
      BPF_STMT(BPF_RET + BPF_K, SECCOMP_RET_ALLOW),
  };
  struct sock_fprog prog = {
      .len = (unsigned short)(sizeof(filter) / sizeof(filter[0])),
      .filter = filter,
  };
  if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)) {
    return 1;
  }
  if (prctl(PR_SET_SECCOMP, 2, &prog)) {
    return 1;
  }
  return 0;
}
```

3. For all of the system calls which can be filtered add one line similar to
below in the function starting the serving phase.

```
install_filter(__NR_execve, AUDIT_ARCH_X86_64, EPERM);
```

4. After installing all the required filters, add the following line to
prevent further manipulation of seccomp filters:
```
revoke_seccomp_manipulation(0);
```
