function fo()
{
    setTimeout(()=>{
    console.log("vanakkam");
},1000)

}
function fi()
{
    fo();
}
fi(); 
var a =200;
var b = 10;

let arr = [1,2,3,2,50];
console.log(arr);
arr.push(100);
console.log(arr);
arr.pop();
console.log(arr);
let nr = arr.map(x => x);
console.log(nr);
let lr = arr.filter(x=>x>10);
console.log(lr);

let marks = 100;
let grade ="";
switch(true)
{
    case marks>80:
        grade="A";
        break;
    case marks>60:
        grade="B";
        break;
    case marks>40:
        grade="c";
        break;
    default:
        grade="Fail";
}
console.log(grade);

console.log(Math.ceil(Math.random()*10)+1);