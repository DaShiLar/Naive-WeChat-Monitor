    var hhh = new Vue({
    el: '#example',
    data: {
        survey_type: 0,           //当前问卷的类型
        count: 0,               //表示已经选择的数量
        search_item: "",         //搜索项
        friendList: [],          //搜索之后显示的名单
        completeFriendList: [],  //还可选的名单（不加任何搜索项）
        max_need_number: 0,   //当前问卷选择最多的人数
        min_need_number: 0,   //当前问卷可选择的最少人数
        selectList: []   //存储的是nickname的list，显示给用户UI的是remarkname的list
    },
    methods: {
        remove_item: function (index) {
            ++this.count;
            var deleteRemarkName = this.friendList[index].RemarkName;
            alert("好友 " + deleteRemarkName + "已选择，已经选择" + this.count + "个好友");
            this.selectList.push(this.friendList[index].NickName);

            //寻找这个人在completeFriendList中的位置
            for (var position_in_complete = 0; position_in_complete < this.completeFriendList.length; position_in_complete++){
                if (this.completeFriendList[position_in_complete].RemarkName==deleteRemarkName){
                     //从完全列表和显示列表中删除这两个人
                    this.completeFriendList.splice(position_in_complete,1);
                    this.friendList.splice(index,1);
                    break;
                }

            }


            var that = this;
            //人数到达上限，自动提交
            if (this.max_need_number == this.count) {
               $.ajax({
                        url: "/survey",
                        method: "POST",
                        data: {
                            "select_list": that.selectList,
                            "survey_type": that.survey_type
                        },
                        success: function (res) {
                            console.log(res);
                            window.location.href = "/survey?survey_type="+res;
                        }
                    });
            }
            //达到最小人数上限的时候，需要询问用户是否还要继续
            if (this.count >= this.min_need_number && this.count < this.max_need_number) {
                res = confirm("已经选择" + this.count + "个好友，是否还要继续选择?");
                if (!res) {
                    $.ajax({
                        url: "/survey",
                        method: "POST",
                        data: {
                            "select_list": that.selectList,
                            "survey_type": that.survey_type
                        },
                        success: function (res) {
                            console.log(res);
                            window.location.href = "/survey?survey_type="+res;
                        }
                    });
                }
            }
        },


        search: function () {

            // 清空重装
            this.friendList = [];

            for (var i = 0; i < this.completeFriendList.length; i++) {
                if (this.completeFriendList[i]['RemarkName'].indexOf(this.search_item) >= 0) {
                    this.friendList.push(this.completeFriendList[i])
                }
            }
            console.log(this.friendList)
        }
    },
    beforeCreate: function () {
        that = this;
        $.ajax({
            url: '/api/friendList',
            method: 'GET',
            dataType: 'json',
            success: function (res) {
                that.completeFriendList = res;
                that.friendList = res;
                that.min_need_number = $('#min_need_number').text();
                that.max_need_number = $('#max_need_number').text();
                that.survey_type = $('#survey_type').text();
            },
            fail: function (res) {
                alert("获取列表失败失败");
            }
        });
    }
});