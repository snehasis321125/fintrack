function createPie(categories){
new Chart(document.getElementById('pieChart'),{
type:'doughnut',
data:{
labels:categories.map(c=>c[0]),
datasets:[{
data:categories.map(c=>c[1])
}]
}
})
}

function createLine(lastWeek){
new Chart(document.getElementById('lineChart'),{
type:'line',
data:{
labels:lastWeek.map(d=>d[1]),
datasets:[{
data:lastWeek.map(d=>d[0])
}]
}
})
}