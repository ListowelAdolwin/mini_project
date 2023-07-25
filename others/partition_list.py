class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

dummy = ListNode(1)
dummy.next = ListNode(5)
dummy.next.next = ListNode(2)
dummy.next.next.next = ListNode(9)
dummy.next.next.next.next = ListNode(0)

class Solution:
    def partition(self, head, x):
        if head is None:
            return head

        head_c = head
        last = head
        while last.next:
            last = last.next

        while head.next:
            if head.next.val > x:
                last.next = head.next
                last = last.next
                last.next = None
                if head.next.next:
                    head.next = head.next.next
                else:
                    head.next = None
            head = head.next
            if not head:
                return
        return head_c

sol = Solution()
print(sol.partition(dummy, 4))
