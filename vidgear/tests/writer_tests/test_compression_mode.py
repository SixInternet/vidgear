from vidgear.gears import WriteGear
import sys
import numpy as np
import os
from numpy.testing import assert_equal
from vidgear.gears.helper import capPropId
from vidgear.gears.helper import check_output
import pytest
import cv2

def return_static_ffmpeg():
	path = ''
	if os.name == 'nt':
		path += os.path.join(os.environ['USERPROFILE'],'download/FFmpeg_static/ffmpeg/bin/ffmpeg.exe')
	else:
		path += os.path.join(os.environ['HOME'],'download/FFmpeg_static/ffmpeg/ffmpeg')
	return os.path.abspath(path)

def return_testvideo_path():
	path = '{}/download/Test_videos/BigBuckBunny.mp4'.format(os.environ['USERPROFILE'] if os.name == 'nt' else os.environ['HOME'])
	return os.path.abspath(path)


def getFrameRate(path):
	process = subprocess.Popen([return_static_ffmpeg(), "-i", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	stdout, _ = process.communicate()
	output =  stdout.decode()
	match_dict = re.search(r"\s(?P<fps>[\d\.]+?)\stbr", output).groupdict()
	return float(match_dict["fps"])

@pytest.mark.xfail(raises=AssertionError)
def test_input_framerate():
	stream = cv2.VideoCapture(return_testvideo_path()) #Open live webcam video stream on first index(i.e. 0) device
	test_video_framerate = stream.get(cv2.CAP_PROP_FPS)
	output_params = {"-input_framerate":test_video_framerate}
	writer = WriteGear(output_filename = 'Output.mp4', **output_params) #Define writer 
	# infinite loop
	while True:
		(grabbed, frame) = stream.read()
		# read frames
		# check if frame is None
		# check if frame empty
		if not grabbed:
			#if True break the infinite loop
			break
		writer.write(frame) 
	stream.release()
	writer.close()
	output_video_framerate = getFrameRate(os.path.abspath('Output.mp4'))
	assert test_video_framerate == output_video_framerate
	os.remove(os.path.abspath('Output.mp4'))

@pytest.mark.xfail(raises=AssertionError)
@pytest.mark.parametrize('conversion', ['COLOR_BGR2GRAY', '', 'COLOR_BGR2YUV', 'COLOR_BGR2BGRA', 'COLOR_BGR2RGB', 'COLOR_BGR2RGBA'])
def test_write(conversion):
	stream = cv2.VideoCapture(return_testvideo_path()) #Open live webcam video stream on first index(i.e. 0) device
	writer = WriteGear(output_filename = 'Output.mp4') #Define writer
	while True:
		(grabbed, frame) = stream.read()
		# read frames
		# check if frame empty
		if not grabbed:
			#if True break the infinite loop
			break
		if conversion:
			frame = cv2.cvtColor(frame, capPropId(conversion))
		
		if conversion in ['COLOR_BGR2RGB', 'COLOR_BGR2RGBA']:
			writer.write(frame, rgb_mode = True)
		else:
			writer.write(frame)
	stream.release()
	writer.close()
	basepath, _ = os.path.split(return_static_ffmpeg()) #extract file base path for debugging aheadget
	ffprobe_path  = os.path.join(basepath,{}.format('ffprobe.exe' if os.name == 'nt' else 'ffprobe'))
	version = check_output([ffprobe_path, "-v", "error", "-count_frames", "-i", os.path.abspath('Output.mp4')])
	for i in ["Error", "Invalid", "error", "invalid"]:
		assert not(i in version)
	os.remove(os.path.abspath('Output.mp4'))

@pytest.mark.xfail(raises=AssertionError)
def test_output_dimensions():
	dimensions = (640,480)
	stream = cv2.VideoCapture(return_testvideo_path()) #Open live webcam video stream on first index(i.e. 0) device
	output_params = {"-output_dimensions":dimensions}
	writer = WriteGear(output_filename = 'Output.mp4') #Define writer
	while True:
		(grabbed, frame) = stream.read()
		# read frames
		# check if frame empty
		if not grabbed:
			#if True break the infinite loop
			break
		writer.write(frame)
	stream.release()
	writer.close()
	
	output = cv2.VideoCapture(os.path.abspath('Output.mp4'))
	output_dim = (output.get(cv2.CAP_PROP_FRAME_WIDTH), output.get(cv2.CAP_PROP_FRAME_HEIGHT))

	assert output_dim[0] == 640 and output_dim[1] == 480
	os.remove(os.path.abspath('Output.mp4'))

test_data_class = [
	('','', {}, False),
	('Output.mp4','', {}, True),
	(os.path.abspath('../'),'', {}, True),
	('Output.mp4','', {"-vcodec":"libx264", "-crf": 0, "-preset": "fast"}, True),
	('Output.mp4', return_static_ffmpeg(), {"-vcodec":"libx264", "-crf": 0, "-preset": "fast"}, True),
	('Output.mp4','wrong_test_path', {" -vcodec  ":" libx264", "   -crf": 0, "-preset    ": " fast "}, False)]
@pytest.mark.parametrize('f_name, c_ffmpeg, output_params, result', test_data_class)
def test_WriteGear_compression(f_name, c_ffmpeg, output_params, result):
	try:
		writer = WriteGear(output_filename = f_name, compression_mode = True , custom_ffmpeg = c_ffmpeg, logging = True, **output_params)
		np.random.seed(0)
		test_data = np.random.random(size=(10, 480, 640, 3)) * 255
		test_data = test_data.astype(np.uint8)
		for i in range(10):
			writer.write(test_data[i])
		writer.close()
		os.remove(os.path.abspath(f_name))
	except Exception as e:
		if result:
			pytest.fail(str(e))