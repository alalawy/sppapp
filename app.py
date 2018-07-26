from flask import Flask, render_template, request, url_for, redirect, make_response
from datetime import datetime
from flask_mysqldb import MySQL
import re
from passlib.hash import sha256_crypt
import pdfkit
import pandas as pd
from werkzeug import secure_filename

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'alphacsoft'
app.config['MYSQL_PASSWORD'] = '14091996Aa'
app.config['MYSQL_DB'] = 'sppapp'
mysql = MySQL(app)

#View & Read
@app.route('/')
def home():
    return render_template('index.html')
    
@app.route('/login')
def login():
    return render_template('app/login.html')

@app.route('/dashboard')
def dashboard():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(id) FROM siswa WHERE status LIKE '1'")
    rv = cur.fetchall()

    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT ((SELECT SUM(jumlah_bayar) FROM iuranlog WHERE jenis_bayar LIKE '1' AND status LIKE '1')/((SELECT SUM(kesanggupan) FROM siswa WHERE status LIKE '1')*12))*100 AS total")
    rv2 = cur2.fetchall()

    cur3 = mysql.connection.cursor()
    cur3.execute("SELECT SUM(tabung_in)-SUM(tabung_out) FROM tabunganlog WHERE status LIKE '1'")
    rv3 = cur3.fetchall()

    return render_template('app/dashboard.html', siswacount=rv, total=rv2, tabung=rv3, rupiah=formatrupiah)

@app.route('/data/siswa')
def datasiswa():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE status LIKE '1'")
    rv = cur.fetchall()
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT * FROM kelas WHERE status LIKE '1'")
    rv2 = cur2.fetchall()

    return render_template('app/dataSiswa.html', siswa=rv, kelas=rv2, rupiah=formatrupiah)

@app.route('/data/kelas')
def datakelas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM kelas WHERE status LIKE '1'")
    rv = cur.fetchall()

    return render_template('app/dataKelas.html', kelas=rv)

@app.route('/data/iuran')
def dataiuran():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    cur = mysql.connection.cursor()
    cur.execute("SELECT nis,nama,kelas,(SELECT kesanggupan * 12)-(SELECT SUM(jumlah_bayar) FROM iuranlog WHERE id_siswa LIKE siswa.id AND jenis_bayar LIKE '1'),((SELECT jumlah FROM jenisiuran WHERE id LIKE '2'))-(SELECT SUM(jumlah_bayar) FROM iuranlog WHERE id_siswa LIKE siswa.id AND jenis_bayar LIKE '2'),((SELECT jumlah FROM jenisiuran WHERE id LIKE '3'))-(SELECT SUM(jumlah_bayar) FROM iuranlog WHERE id_siswa LIKE siswa.id AND jenis_bayar LIKE '3') FROM siswa WHERE status LIKE '1'")
    rv = cur.fetchall()

    return render_template('app/dataIuran.html', siswa=rv, rupiah=formatrupiah)

@app.route('/data/tabungan')
def datatabungan():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    cur = mysql.connection.cursor()
    cur.execute("SELECT nis,nama,kelas,((SELECT SUM(tabung_in) FROM tabunganlog WHERE id_siswa LIKE siswa.id)-(SELECT SUM(tabung_out) FROM tabunganlog WHERE id_siswa LIKE siswa.id)) FROM siswa WHERE status LIKE '1'")
    rv = cur.fetchall()

    return render_template('app/dataTabungan.html', siswa=rv, rupiah=formatrupiah)

@app.route('/transaksi/iuran')
def transaksiiuran():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    cur = mysql.connection.cursor()
    cur.execute("SELECT id,tanggal,(SELECT nama FROM siswa WHERE id LIKE iuranLog.id_siswa),(SELECT kelas FROM siswa WHERE id LIKE iuranLog.id_siswa),(SELECT nama FROM jenisIuran WHERE id LIKE iuranLog.jenis_bayar),jumlah_bayar,diskon, keterangan FROM iuranLog WHERE status LIKE '1' ORDER BY id DESC")
    rv = cur.fetchall()

    return render_template('app/transaksiIuran.html', iuran=rv, rupiah=formatrupiah)

@app.route('/transaksi/tabungan')
def transaksitabungan():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    cur = mysql.connection.cursor()
    cur.execute("SELECT id,tanggal,(SELECT nama FROM siswa WHERE id LIKE tabunganlog.id_siswa),(SELECT kelas FROM siswa WHERE id LIKE tabunganlog.id_siswa),tabung_in,tabung_out FROM tabunganlog WHERE status LIKE '1' ORDER BY id DESC")
    rv = cur.fetchall()

    return render_template('app/transaksiTabungan.html', tabung=rv, rupiah=formatrupiah)

@app.route('/data/trash')
def datasiswatrash():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE status LIKE '0'")
    rv = cur.fetchall()
    cur.close()
    return render_template('app/trash.html', siswa=rv)

@app.route('/transaksi/bayar', methods=["POST"])
def bayar():
    idSiswa = request.form['idSiswa'] or ""

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE nis LIKE '%"+idSiswa+"%' AND status LIKE '1'")
    rv = cur.fetchall()
    cur.close()

    return render_template('app/bayarIuran.html', siswa=rv)

@app.route('/transaksi/setor', methods=["POST"])
def setor():
    idSiswa = request.form['idSiswa'] or ""

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE nis LIKE '%"+idSiswa+"%' AND status LIKE '1'")
    rv = cur.fetchall()
    cur.close()

    return render_template('app/bayarTabungan.html', siswa=rv)

@app.route('/transaksi/tarik', methods=["POST"])
def tarik():
    idSiswa = request.form['idSiswa'] or ""

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE nis LIKE '%"+idSiswa+"%' AND status LIKE '1'")
    rv = cur.fetchall()
    cur.close()

    return render_template('app/tarikTabungan.html', siswa=rv)

@app.route('/edit/siswa', methods=["POST"])
def editsiswa():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    idSiswa = request.form['idSiswa'] or ""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE id LIKE %s AND status LIKE '1'", (idSiswa,))
    rv = cur.fetchall()
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT * FROM kelas WHERE status LIKE '1'")
    rv2 = cur2.fetchall()

    return render_template('app/editSiswa.html', siswa=rv, kelas=rv2, rupiah=formatrupiah)


#Create Data
@app.route('/add/siswa', methods=["POST"])
def addsiswa():
    nis = request.form['nis'] or ""
    nama = request.form['nama'] or ""
    alamat = request.form['alamat'] or ""
    kelas = request.form['kelas'] or ""
    tempatLahir = request.form['tempatLahir'] or ""
    tanggalLahir = request.form['tanggalLahir'] or ""
    ortu = request.form['ortu'] or ""
    nohp = request.form['nohp'] or ""
    kesanggupan = re.sub(r'\D', "", request.form['kesanggupan'] or "")
    username = request.form['username'] or ""
    password = request.form['password'] or ""
    password256 = sha256_crypt.encrypt(password)
    timestamp = str(datetime.now())
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO siswa (nis,nama,alamat,kelas,tempat_lahir,tanggal_lahir,nama_ortu,no_hp,kesanggupan,username,password,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'1')", (nis,nama,alamat,kelas,tempatLahir,tanggalLahir,ortu,nohp,kesanggupan,username,password,))
    mysql.connection.commit()
    return redirect(url_for('datasiswa'))

@app.route('/add/kelas', methods=["POST"])
def addkelas():
    nama = request.form['namaKelas'] or ""
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO kelas (namaKelas,status) VALUES (%s,'1')", (nama,))
    mysql.connection.commit()
    return redirect(url_for('datakelas'))

@app.route('/add/bayar', methods=["POST"])
def addbayar():
    tanggal = request.form['tanggal'] or ""
    idSiswa = request.form['idSiswa'] or ""
    jenisBayar = request.form['jenisBayar'] or ""
    jumlahUang = re.sub(r'\D', "", request.form['jumlahUang'] or "")
    diskon = re.sub(r'\D', "", request.form['diskon'] or "")
    dari = request.form['dari']
    sampai =  request.form['sampai']

    bulanArr = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    bulan = ""
    for i in range(int(dari), int(sampai)+1):
        bulan = bulan + bulanArr[i] + ", "

    
    keterangan = request.form['keterangan'] + str(bulan)

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO iuranlog (tanggal,id_siswa,jenis_bayar,jumlah_bayar,diskon,keterangan,status) VALUES (%s, %s, %s, %s, %s, %s, '1')", (tanggal, idSiswa, jenisBayar, jumlahUang, diskon,keterangan))
    mysql.connection.commit()
    return redirect(url_for('transaksiiuran'))


@app.route('/add/setor', methods=["POST"])
def addsetor():
    tanggal = request.form['tanggal'] or ""
    idSiswa = request.form['idSiswa'] or ""
    jumlahUang = re.sub(r'\D', "", request.form['jumlahUang'] or "")

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO tabunganlog (tanggal,id_siswa,tabung_in,status) VALUES (%s, %s, %s, '1')", (tanggal, idSiswa, jumlahUang,))
    mysql.connection.commit()
    return redirect(url_for('transaksitabungan'))

@app.route('/add/tarik', methods=["POST"])
def addtarik():
    tanggal = request.form['tanggal'] or ""
    idSiswa = request.form['idSiswa'] or ""
    jumlahUang = re.sub(r'\D', "", request.form['jumlahUang'] or "")

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO tabunganlog (tanggal,id_siswa,tabung_out,status) VALUES (%s, %s, %s, '1')", (tanggal, idSiswa, jumlahUang,))
    mysql.connection.commit()
    return redirect(url_for('transaksitabungan'))

@app.route('/add/siswa/import', methods=["GET","POST"])
def importsiswa():

    fileExcel = request.files['fileexcel']
    fileExcel.save(secure_filename(fileExcel.filename))

    DataFrame = pd.read_excel(fileExcel.filename, sheet_name=0)

    for i in range(0, len(DataFrame)):
        nis = DataFrame['NIS'][i]
        nama = DataFrame['NAMA'][i]
        alamat = DataFrame['ALAMAT'][i]
        kelas = DataFrame['KELAS'][i]
        tempatLahir = DataFrame['TEMPAT LAHIR'][i]
        tanggalLahir = DataFrame['TANGGAL LAHIR'][i]
        ortu = DataFrame['NAMA ORANG TUA'][i]
        nohp = DataFrame['NOMOR HP ORTU'][i]
        kesanggupan = DataFrame['KESANGGUPAN SPP'][i]
        username = DataFrame['USERNAME'][i]
        password = DataFrame['PASSWORD'][i]
        timestamp = str(datetime.now())
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO siswa (nis,nama,alamat,kelas,tempat_lahir,tanggal_lahir,nama_ortu,no_hp,kesanggupan,username,password,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'1')", (nis,nama,alamat,kelas,tempatLahir,tanggalLahir,ortu,nohp,kesanggupan,username,password,))
        mysql.connection.commit()

    return redirect(url_for('datasiswa'))

#Delete Data
@app.route('/hapus/siswa/<string:id_data>', methods=["GET"])
def hapusbarang(id_data):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE siswa SET status='0' WHERE id LIKE %s", (id_data,))
    cur.connection.commit()
    return redirect(url_for('datasiswa'))

@app.route('/hapus/kelas/<string:id_data>', methods=["GET"])
def hapuskelas(id_data):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE kelas SET status='0' WHERE id LIKE %s", (id_data,))
    cur.connection.commit()
    return redirect(url_for('datakelas'))


#Restore Data
@app.route('/restore/siswa/<string:id_data>', methods=["GET"])
def restorebarang(id_data):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE siswa SET status='1' WHERE id LIKE %s", (id_data,))
    cur.connection.commit()
    return redirect(url_for('datasiswatrash'))

@app.route('/restore/kelas/<string:id_data>', methods=["GET"])
def restorekelas(id_data):
    cur = mysql.connection.cursor()
    cur.execute("UPDATE kelas SET status='1' WHERE id LIKE %s", (id_data,))
    cur.connection.commit()
    return redirect(url_for('datasiswatrash'))

#Update Data
@app.route('/add/siswa', methods=["POST"])
def updatesiswa():
    nis = request.form['nis'] or ""
    nama = request.form['nama'] or ""
    alamat = request.form['alamat'] or ""
    kelas = request.form['kelas'] or ""
    tempatLahir = request.form['tempatLahir'] or ""
    tanggalLahir = request.form['tanggalLahir'] or ""
    ortu = request.form['ortu'] or ""
    nohp = request.form['nohp'] or ""
    kesanggupan = re.sub(r'\D', "", request.form['kesanggupan'] or "")
    username = request.form['username'] or ""
    password = request.form['password'] or ""
    password256 = sha256_crypt.encrypt(password)
    timestamp = str(datetime.now())
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO siswa (nis,nama,alamat,kelas,tempat_lahir,tanggal_lahir,nama_ortu,no_hp,kesanggupan,username,password,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'1')", (nis,nama,alamat,kelas,tempatLahir,tanggalLahir,ortu,nohp,kesanggupan,username,password,))
    mysql.connection.commit()
    return redirect(url_for('datasiswa'))


#Report
@app.route('/report/kartu')
def reportkartu():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE status LIKE '1'")
    cur.connection.commit()
    rv = cur.fetchall()

    rendered = render_template('report/kartupelajar.html', siswa=rv)
    pdf = pdfkit.from_string(rendered, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=kartuiuran.pdf'

    return response

@app.route('/report/siswa')
def reportsiswa():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM siswa WHERE status LIKE '1'")
    rv = cur.fetchall()
    cur2 = mysql.connection.cursor()
    cur2.execute("SELECT * FROM kelas WHERE status LIKE '1'")
    rv2 = cur2.fetchall()

    rendered = render_template('report/dataSiswa.html', siswa=rv, kelas=rv2, rupiah=formatrupiah)
    pdf = pdfkit.from_string(rendered, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=datasiswa.pdf'

    return response

@app.route('/report/kwitansi', methods=['POST'])
def reportkwitansi():
    def formatrupiah(uang):
        y = str(uang)
        if len(y) <= 3 :
            return 'Rp. ' + y     
        else :
            p = y[-3:]
            q = y[:-3]
            return   formatrupiah(q) + '.' + p

    id = request.form['id_iuran'] or ""
    cur = mysql.connection.cursor()
    cur.execute("SELECT tanggal,(SELECT nama FROM siswa WHERE id LIKE iuranlog.id_siswa),(SELECT nama FROM jenisiuran WHERE id LIKE iuranlog.jenis_bayar),jumlah_bayar,diskon,keterangan FROM iuranlog WHERE status LIKE '1' and id LIKE %s", (id,))
    rv = cur.fetchall()

    now = str(datetime.now())

    rendered = render_template('report/kwitansi.html', siswa=rv, rupiah=formatrupiah, tanggal=now, namaBendahara="Ahmad Mugni, S.E.I")
    pdf = pdfkit.from_string(rendered, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=kwitansi-iuran.pdf'

    return response


if __name__ == "__main__":
    app.run(debug=True)