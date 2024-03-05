function render_keyword_data(data) {
    console.log(1)
    console.log(data)
    var keyword_table = document.getElementById('keyword-table');
    keyword_table.innerHTML = "";
    console.log(Object.keys(data).length);
    keys = Object.keys(data);
    for (var i = 0; i < keys.length; i++) {
        keyword_table.innerHTML += '<tr><td>' + keys[i] + '</td><td>' + data[keys[i]] + '</td></tr>'
    }
}


function get_data() {
    fetch('http://127.0.0.1:5600/get_api', { mode: 'cors' })
        .then((res) => (res.json()))
        .then((res) => {
            // console.log(res);
            res = res['data']
            //res[0]分類1的資料
            //res[1]分類2的資料
            //res[2]分類3的資料
            //res[3]分類4的資料
            //res[4]時間

            // console.log(res[2])
            console.log(res)
            // // 
            render_chart(res);

        })
    fetch('http://127.0.0.1:5600/get_keyword_api', { mode: 'cors' })
        .then((res) => (res.json()))
        .then((res) => {
            // console.log(res);
            res = res['data']
            // res[0]=res[0]//分類1的資料
            // res[1]=res[1]//分類2的資料
            // res[2]=res[2]//分類3的資料
            // res[3]=res[2]//分類4的資料
            // res[4]=res[2]//時間

            // console.log(res[2])
            // console.log(res)
            // 
            render_keyword_data(res);

        })

}
get_data()
