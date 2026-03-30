.section .text
.global _start
_start:
call main
mov rax, 60
mov rdi, 0
syscall
func_test_semantic:
push rbp
mov rbp, rsp
func_test_semantic:
mov [rbp-16], 5
mov [rbp-128], 10
mov [rbp-40], [rbp-16]
add [rbp-40], [rbp-128]
mov [rbp-8], [rbp-40]
mov [rbp-64], [rbp-16]
imul [rbp-64], [rbp-128]
mov [rbp-0], [rbp-64]
cmp [rbp-16], [rbp-128]
setg al
movzx [rbp-80], al
test [rbp-80], [rbp-80]
jz L0
mov [rbp-40], [rbp-16]
sub [rbp-40], [rbp-128]
mov [rbp-112], [rbp-40]
jmp L1
L0:
mov [rbp-40], [rbp-128]
sub [rbp-40], [rbp-16]
mov [rbp-112], [rbp-40]
L1:
L2:
cmp [rbp-16], 10
setl al
movzx [rbp-88], al
test [rbp-88], [rbp-88]
jz L3
mov [rbp-40], [rbp-16]
add [rbp-40], 1
mov [rbp-16], [rbp-40]
jmp L2
L3:
push [rbp-16]
push [rbp-128]
call func_add
mov [rbp-48], rax
mov [rbp-72], [rbp-48]
mov rsp, rbp
pop rbp
ret
func_add:
push rbp
mov rbp, rsp
func_add:
mov [rbp-0], [rbp-24]
add [rbp-0], [rbp-16]
mov rax, [rbp-0]
mov rsp, rbp
pop rbp
ret
mov rsp, rbp
pop rbp
ret