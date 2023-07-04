from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import sys
import math
import scipy
import numpy as np
import scipy.io.wavfile as wavfile
from PyQt5 import QtWidgets, uic, QtCore
import PyQt5.QtMultimedia as QtMultimedia
import pyaudio
import wave
import pyaudio


class Ui(QtWidgets.QMainWindow):

    def __init__(self):
        super(Ui, self).__init__() 
        uic.loadUi('main_spectogram.ui', self) 
        self.reset_combo_box()

        self.file="none"
        self.nfft_value = 256
        self.sound_wave = MplCanvas(width=10, height=10, dpi=100)
        self.is_currently_recording=False

        self.actionChooseFile.triggered.connect(self.load_file)
        self.actionSave.triggered.connect(self.save_to_file)       
        self.actionBroadBand.triggered.connect(self.broad_band_spectrogram)
        self.actionNarrowBand.triggered.connect(self.narrow_band_spectrogram)
        self.recordButton.clicked.connect(self.record_sound)
        self.stopRecordingButton.clicked.connect(self.stop_recording_sound)
        self.actionWelchGraph.triggered.connect(self.welch_graph)
        self.actionLowPass.triggered.connect(self.low_pass_filter)
        self.actionHighPass.triggered.connect(self.high_pass_filter)      
        self.playSoundHiddenButton.clicked.connect(self.play_sound)
        self.generateForFragmentHiddenButton.clicked.connect(self.show_whole)
        self.creatingWindowFunctionButton.clicked.connect(self.my_window_function)
        self.creatingFilterButton.clicked.connect(self.my_filter)
        
        self.generateForFragmentHiddenButton.setHidden(True)
        self.playSoundHiddenButton.setHidden(True)

        self.comboBox.activated.connect(self.combo_box)
        self.nfft_box.valueChanged.connect(self.nfft_change)
        self.noverlap_box.valueChanged.connect(self.noverlap_change)

        self.nfft_box.setValue(self.nfft_value)
        self.noverlap_box.setValue(50)

        self.horizontalLayout.addWidget(self.sound_wave)
        self.show() 
    
    def my_filter(self):
        if self.file=="none":
            return
        text = QtWidgets.QInputDialog.getMultiLineText(self, "Wprowadż kod funkcji","Kod:")
        aud,fs=self.get_audio(self.file)
        filtered_audio = eval(text[0])
        self.create_spectrogram(audio=filtered_audio,nfft=self.nfft_box.value(),fs=fs,window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))

            
    def my_window_function(self):   
        if self.file=="none":
            return
        text = QtWidgets.QInputDialog.getMultiLineText(self, "Wprowadż kod funkcji","Kod:")
        aud,fs=self.get_audio(self.file)
        
        try:
            M = self.nfft_box.value()
            self.create_spectrogram(audio=aud,nfft=M,fs=fs,window=eval(text[0]),
                                        noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Błąd", str(e))
        
    def create_spectrogram(self,audio,nfft,fs,noverlap,window):
        plt.close()
        plt.specgram(audio,NFFT=nfft,Fs=fs,window=window,noverlap=noverlap,cmap="jet")
        plt.xlabel("Czas (s)")
        plt.ylabel("Częstotliwość (hz)")

        while self.horizontalLayout_3.count():
            child=self.horizontalLayout_3.takeAt(0)
            del child
        self.horizontalLayout_3.addWidget(FigureCanvasQTAgg(plt.gcf()))
        
    def low_pass_filter(self):
        if self.file=="none":
            return
        aud,fs=self.get_audio(self.file)
        hz,bool = QtWidgets.QInputDialog.getInt(self,"Ustaw parametry","Ustaw częstotliwość",1000,10,int(fs/2-10))
        b,a=scipy.signal.butter(5, hz, fs=fs, btype='low')
        y = scipy.signal.filtfilt(b, a, aud)
        self.create_spectrogram(audio=y,nfft=self.nfft_box.value(),fs=fs,window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
    

    def high_pass_filter(self):
        if self.file=="none":
            return
        aud,fs=self.get_audio(self.file)

        hz,bool = QtWidgets.QInputDialog.getInt(self,"Ustaw parametry","Ustaw częstotliwość",1000,10,int(fs/2-10))
        b,a=scipy.signal.butter(5, hz, fs=fs, btype='high')
        y = scipy.signal.filtfilt(b, a, aud)
        self.create_spectrogram(audio=y,nfft=self.nfft_box.value(),fs=fs,window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
        
    def welch_graph(self):
        if self.file=="none":
            return
        aud,fs=self.get_audio(self.file) 
        f, Pxx_den = scipy.signal.welch(aud, fs,nfft=self.nfft_box.value(),
                                        window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                        noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
        plt.close()
        plt.semilogy(f, Pxx_den)
        plt.xlabel('[Hz]')
        plt.ylabel('[V**2/Hz]')
        plt.tight_layout()
        while self.horizontalLayout_3.count():
                child=self.horizontalLayout_3.takeAt(0)
                del child
        self.horizontalLayout_3.addWidget(FigureCanvasQTAgg(plt.gcf()))

    def stop_recording_sound(self):
        self.is_currently_recording=True
        self.stopRecordingButton.setText("Zakończ nagrywanie | |")       
        
    def record_sound(self):
        self.stopRecordingButton.setText("Zakończ nagrywanie |>")
        audio=pyaudio.PyAudio()
        stream=audio.open(format=pyaudio.paInt16,channels=1,rate=44100,input=True,frames_per_buffer=1024)
        frames=[]
        
        while self.is_currently_recording==False:       
            data = stream.read(1024)
            frames.append(data)
            QtWidgets.QApplication.processEvents()

        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        sound_file=wave.open("recording.wav","wb")
        sound_file.setnchannels(1)
        sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        sound_file.setframerate(44100)
        sound_file.writeframes(b''.join(frames))
        sound_file.close()
        
        self.file="recording.wav"
        self.generate_spectogram()
        self.is_currently_recording=False
        
        
    def show_whole(self):
        self.generateForFragmentHiddenButton.setHidden(True)
        self.generate_spectogram()
    
    def load_file(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setWindowTitle("Wczytaj plik")
        dialog.setNameFilter("Pliki dzwiekowe (*.wav)")
        dialog.exec()
        if len(dialog.selectedFiles())==0:
            return
        file = dialog.selectedFiles().pop()
        self.file=file
        self.generate_spectogram()
    
    def broad_band_spectrogram(self):
        if self.file!="none":
            plt.close()
            aud, fs = self.get_audio(self.file)
            self.nfft_value=int(len(aud)/fs*33)
            self.create_spectrogram(aud,nfft=self.nfft_value,fs=fs,noverlap=int(self.nfft_value/2),
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_value))
            self.nfft_box.blockSignals(True)
            self.nfft_box.setValue(self.nfft_value)
            self.nfft_box.blockSignals(False)
            self.noverlap_box.blockSignals(True)
            self.noverlap_box.setValue(int(self.nfft_value/2))
            self.noverlap_box.blockSignals(False)
        
    def narrow_band_spectrogram(self):
        if self.file!="none":
            plt.close()
            aud, fs = self.get_audio(self.file)
            self.nfft_value=int(len(aud)/fs*200)
            self.create_spectrogram(aud,nfft=self.nfft_value,fs=fs,noverlap=int(self.nfft_value/2),
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_value))
            self.nfft_box.blockSignals(True)
            self.nfft_box.setValue(self.nfft_value)
            self.nfft_box.blockSignals(False)
            self.noverlap_box.blockSignals(True)
            self.noverlap_box.setValue(int(self.nfft_value/2))
            self.noverlap_box.blockSignals(False)


    def nfft_change(self):
        if self.nfft_box.value()<self.nfft_value and self.nfft_value>2:
            self.nfft_value=int(self.nfft_value/2)
            self.nfft_box.blockSignals(True)
            self.nfft_box.setValue(self.nfft_value)
            self.nfft_box.blockSignals(False)
        else:
            self.nfft_value*=2
            self.nfft_box.blockSignals(True)
            self.nfft_box.setValue(self.nfft_value)
            self.nfft_box.blockSignals(False)


        if self.file!="none":
            plt.close()
            aud, fs = self.get_audio(self.file)
            self.create_spectrogram(audio=aud,nfft=self.nfft_box.value(),fs=fs,
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                    noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))

    def noverlap_change(self):
        if self.file!="none":
            plt.close()
            aud, fs = self.get_audio(self.file)
            self.create_spectrogram(audio=aud,nfft=self.nfft_box.value(),fs=fs,
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                    noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
    
    def onselect(self,xmin, xmax):
        self.xmin=xmin
        self.xmax=xmax
        self.generateForFragmentHiddenButton.setHidden(False)
        self.playSoundHiddenButton.setHidden(False)

        fragment, fs = self.get_audio(self.file)
        fragment=fragment[math.floor(self.xmin):math.ceil(self.xmax)]
        self.create_spectrogram(audio=fragment,nfft=self.nfft_box.value(),fs=fs,
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                    noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))
        

    def play_sound(self):

        aud, fs = self.get_audio(self.file)           
        fragment=aud[math.floor(self.xmin):math.ceil(self.xmax)]
        
        wavfile.write("temp.wav",fs,fragment)
        QtMultimedia.QSound.play("temp.wav")
        self.playSoundHiddenButton.setHidden(True)


    def generate_spectogram(self):
        aud, fs = self.get_audio(self.file)

        old = self.horizontalLayout.takeAt(0)
        del old
        self.sound_wave = MplCanvas(self, width=10, height=10, dpi=100)
        self.horizontalLayout.addWidget(self.sound_wave)
        self.sound_wave.axes.plot(aud)
        
        self.span = SpanSelector(self.sound_wave.axes,self.onselect,'horizontal',
                                 useblit=True,props=dict(alpha=0.5,facecolor="tab:blue"),interactive=True,drag_from_anywhere=True)
        
        self.create_spectrogram(audio=aud,nfft=256,fs=fs,window=scipy.signal.get_window("blackman",256),noverlap=128)

    def save_to_file(self):
        file = QtWidgets.QFileDialog.getSaveFileName(self,"Zapisz do pliku",filter="Obraz (*.png)")
        plt.savefig(file[0])

    def reset_combo_box(self):
        
        lista = {"hamming","bartlett","blackman","triang","boxcar","flattop","parzen","tukey"}
        self.comboBox.addItems(lista)

    def combo_box(self):
        if self.file=="none":
            return
        aud, fs = self.get_audio(self.file)
        self.create_spectrogram(audio=aud,nfft=self.nfft_box.value(),fs=fs,
                                    window=scipy.signal.get_window(self.comboBox.currentText(),self.nfft_box.value()),
                                    noverlap=math.floor(self.noverlap_box.value()/100*self.nfft_box.value()))

    def get_audio(self, name):
            fs, aud = wavfile.read(name)
            if len(aud.shape)==1:
                aud = aud[:]
            else:
                aud=aud[:,0]

            return (aud,fs)

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        self.axes.axis('off')
        super(MplCanvas, self).__init__(fig)

if __name__ == "__main__":  

    app = QtWidgets.QApplication(sys.argv) 
    window = Ui() 
    window.setWindowTitle("Spektrogram")
    app.exec()

