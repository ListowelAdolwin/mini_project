def bubble_sort(arr):
    print(arr)
    for i in range(len(arr)):
        for j in range(len(arr)):
            if arr[j] > arr[i]:
                arr[i], arr[j] = arr[j], arr[i]

    print(arr)

def selection_sort(arr):
    print(arr)
    for i in range(len(arr)):
        minn = i
        for j in range(i + 1, len(arr)):
            if arr[j] < arr[minn]:
                minn = j
        if minn != i:
            arr[minn], arr[i] = arr[i], arr[minn]
    print(arr)

def insertion_sort(arr):
    print(arr)
    for i in range(1, len(arr)):
        j = i - 1
        swap = i
        while j >= 0:
            if arr[j] > arr[swap]:
                arr[j], arr[swap] = arr[swap], arr[j]
                swap = j
                j -= 1
            else:
                break
    print(arr)


arr =[4,2,1,3]
insertion_arr = [4,2,0,-3,345,-241,3]
bubble_arr = [4,2,1,3]
selection_arr = [4,2,1,3]
#print(arr.sort())
bubble_sort(bubble_arr)
selection_sort(selection_arr)
insertion_sort(insertion_arr)
