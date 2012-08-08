<!DOCTYPE html>
<html>
<head>
    <title>Test upload</title>
</head>
<body>
    <h2>Select files to upload</h2>
        <form id="upload" name="upload" method="POST" enctype="multipart/form-data" action="/upload">
        <div>
            <input type="file" name="file1">
        </div>

        <!-- <br>
        <input type="file" name="file2"><br>
        <input type="file" name="file3"><br>
        <input type="file" name="file4"><br>
        <input type="file" name="file5"><br>
        <input type="file" name="file6"><br> -->
        <button class="submit" onclick="return uploader.startUpload();">Submit</button>
        <button class="cancel" onclick="return uploader.cancelUpload();" disabled>Cancel</button>
        <input type="hidden" name="test" value="value">
    </form>
    <div id="progresswrap">
        <div id="progress" style="clear:both;">
            <div id="progressbar"> </div>
        </div>
        <div id="tp">0%</div>
        <div><span id="speed">0</span> kb/s<div>
        <div id="resultinfo"></div>
    </div>
<style type="text/css">
    input {
        margin: 5px;
    }
    #progresswrap {
        width: 480px;
    }
    #progress {
        float:left;
        width: 400px;
        height:20px;
        border: 1px
        solid black
    }
    #progressbar {
        width: 1px;
        height:18px;
        background-color:
        blue; border: 1px solid white;
    }
    #tp {
        position: relative;
        right: -10px;
        overflow: hide;
    }
</style>
<script type="text/javascript">
!function(document, window) {

function Uploader() {
    this.upload_xhr = null;
    this.interval = null;
    this.uuid = "";
    this.ticks = 0;
}


Uploader.prototype = {
    startUpload: function() {
        document.getElementsByClassName("submit")[0].setAttribute('disabled', 'disabled');
        this.uuid = "";
        for (var i = 0; i < 32; i++) {
            this.uuid += Math.floor(Math.random() * 16).toString(16);
        }
        var form = document.forms[0];

        var self = this;
        this.interval = setInterval(
            function () {
                self.ticks += 1;
                self.fetch();
            },
            1000
        );
        var fd = new FormData(form);
        try {
            this.upload_xhr = new XMLHttpRequest();
            xhr = this.upload_xhr;
            xhr.open("POST", "/upload", true);
            xhr.setRequestHeader("X-Progress-ID", this.uuid);
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        document.getElementById("resultinfo").innerHTML = xhr.responseText;
                    }
                }
            }
            xhr.send(fd);
            document.getElementsByClassName("cancel")[0].removeAttribute("disabled");
        } catch(err) {
            console.log(err);
        }
        return false;
    },

    cancelUpload: function() {
        this.upload_xhr.abort();
        this.upload_xhr = null;
        this.uuid = "";
        clearTimeout(this.interval);
        this.interval = null;
        this.ticks = 0;
        document.getElementById("speed").innerHTML = "0";
        document.getElementById("tp").innerHTML = "0%";
        document.getElementById("progressbar").style.width = "1px";
        document.getElementsByClassName("cancel")[0].setAttribute("disabled", "disabled");
        document.getElementsByClassName("submit")[0].removeAttribute("disabled");
        return false;
    },


    fetch: function() {
        var uuid = this.uuid;
        var xhr = new XMLHttpRequest();
        var self = this;
        xhr.open("GET", "/progress", true);
        xhr.setRequestHeader("X-Progress-ID", uuid);
        xhr.onreadystatechange = function () {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    /* poor-man JSON parser */
                    //console.log(xhr.responseText);
                    var upload = JSON.parse(xhr.responseText)
                      , percentage = upload.received / upload.size
                      , rounded = Math.round(percentage*1000)/10

                    document.getElementById('tp').innerHTML = (isNaN(rounded) ? '100' : rounded) + '%';

                    /* change the width if the inner progress-bar */
                    if (upload.state == 'uploading') {
                        console.log(upload);
                        var bar = document.getElementById('progressbar');

                        w = 400 * percentage - 2; // 2px for the border
                        bar.style.width = w + 'px';

                        document.getElementById('speed').innerHTML = Math.round((upload.received / self.ticks) / 1000)
                    }
                    /* we are done, stop the interval */
                    else if (upload.state == 'done') {
                        bar = document.getElementById('progressbar');
                        bar.style.width = '398px'
                        clearTimeout(this.interval);
                    }
                }
            }
        }
        xhr.send(null);
    }

}
window.uploader = new Uploader();


} (document, window);
</script>
</body>
</html>