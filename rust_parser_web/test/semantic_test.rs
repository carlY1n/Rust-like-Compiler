fn test_semantic() {
    let mut a: i32 = 5;
    let b: i32 = 10;

    let c = a + b;
    let d = a * b;
    
    if a > b {
        let e = a - b;
    } else {
        let e = b - a;
    }

    while a < 10 {
        a = a + 1;
    }

    let result = add(a, b);
}

fn add(x: i32, y: i32) -> i32 {
    return x + y;
}

