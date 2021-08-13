#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""   
(c) Research Group CAMMA, University of Strasbourg, France
Website: http://camma.u-strasbg.fr
Code author: Armine Vardazaryan
"""

import tkinter as tk
from tkinter import ttk 
from tkinter import messagebox
from PIL import Image, ImageTk, ImageOps
import os, json
from glob import glob1
from subprocess import Popen
from shutil import which
from pathlib import Path
import cv2

from db_manager import DB_Manager

logo1_path = './images/camma.png'
logo2_path = './images/u_of_strasbourg_small.png'

def get_resized_img(img, video_size):
    """ resize image preserving aspect ratio
    https://stackoverflow.com/a/54314043 """
    width, height = video_size  # these are the MAX dimensions
    video_ratio = width / height
    img_ratio = img.size[0] / img.size[1]
    if video_ratio >= 1:  # the video is wide
        if img_ratio <= video_ratio:  # image is not wide enough
            width_new = int(height * img_ratio)
            size_new = width_new, height
        else:  # image is wider than video
            height_new = int(width / img_ratio)
            size_new = width, height_new
    else:  # the video is tall
        if img_ratio >= video_ratio:  # image is not tall enough
            height_new = int(width / img_ratio)
            size_new = width, height_new
        else:  # image is taller than video
            width_new = int(height * img_ratio)
            size_new = width_new, height
    return img.resize(size_new, resample=Image.LANCZOS)

def is_tool(name):
    """Check whether `name` is on PATH and marked as executable.
    https://stackoverflow.com/a/34177358 """

    return which(name) is not None
	
class Reviewer_Gui_Rater(ttk.Frame):
    
    def __init__(self, datapath, resource_dir, config_path):
        super().__init__()   
                    
        self.dbm = DB_Manager(datapath,'annotations.pickle')
        
        self.logo1_path = os.path.join(resource_dir, 'camma.png')
        self.logo2_path = os.path.join(resource_dir, 'u_of_strasbourg_small.png')
        self.logo3_path = os.path.join(resource_dir, 'ihu.png')
        
        self.config_path = config_path
        
        
        self.initUI()
        
        self.text_editing_mode = False
        
    def on_focus_in(self, event):
        self.text_editing_mode = True
        
    def on_focus_out(self, event):
        self.text_editing_mode = False
        
    def initUI(self):
        width = 6
        
        self.grid(row=0, column=0, columnspan=width, sticky=tk.E+tk.W+tk.N+tk.S)
        
        self.rowconfigure(2, weight=1)
        for i in range(width):
            self.columnconfigure(i, weight=1)
           
        
        self.master.title("CVS Annotator")
        
        frame_ids = ttk.Frame(self,  borderwidth=2)
        frame_ids.grid(row=0, column=0, columnspan=width,sticky=tk.N,padx=10)
        
        goto_frame = ttk.Frame(frame_ids)
        goto_frame.grid(row=0, column=0, columnspan=1, sticky=tk.W)
        
        vid_id_lbl = ttk.Label(goto_frame, text='video: ')
        vid_id_lbl.grid(row=0, column=0, sticky=tk.W+tk.N)
        
        fr = self.dbm.get_id()
        self.vid_id_line = tk.StringVar()
        self.vid_id_entry = tk.Entry(goto_frame, width = 7, textvariable=self.vid_id_line)
        self.vid_id_entry.grid(row=0, column=1, sticky=tk.W)
        self.vid_id_line.set(fr[0])
        self.vid_id_entry.bind("<FocusIn>", self.on_focus_in)
        self.vid_id_entry.bind("<FocusOut>", self.on_focus_out)
        
        frame_id_lbl = ttk.Label(goto_frame, text='frame: ')
        frame_id_lbl.grid(row=0, column=2, sticky=tk.W+tk.N)
        
        self.frame_id_line = tk.StringVar()
        self.frame_id_entry = tk.Entry(goto_frame, width = 7, textvariable=self.frame_id_line)
        self.frame_id_entry.grid(row=0, column=3, sticky=tk.W+tk.N)
        self.frame_id_line.set(fr[1])
        self.frame_id_entry.bind("<FocusIn>", self.on_focus_in)
        self.frame_id_entry.bind("<FocusOut>", self.on_focus_out)
        
        goto_button =ttk.Button(goto_frame, text="GoTo", command=self.goto_callback)
        goto_button.grid(row=0, column=4, sticky=tk.W+tk.N)
        
        
        vid_prog_frame = ttk.Frame(frame_ids)
        vid_prog_frame.grid(row=0, column=5, columnspan=1, sticky=tk.E, padx=100)
        
        openVid_button =ttk.Button(vid_prog_frame, text="Open video", command=self.openVid_callback)
        openVid_button.grid(row=0, column=0, sticky=tk.N+tk.E)
        
        self.progress_line = tk.StringVar()
        progress_lbl = ttk.Label(vid_prog_frame, width=15, textvariable=self.progress_line )
        progress_lbl.grid(row=0, column=1, sticky=tk.N+tk.E)
        progress = self.dbm.get_progress()
        self.progress_line.set('  {} / {}'.format(*progress))
        
        ######################################################
        frame_order = ttk.Frame(self, borderwidth=2)
        
        frame_order.grid(row=1, column=0, columnspan=width,sticky=tk.N)
        
        self.shuffle_flag = False
        self.shffl_button = tk.Button(frame_order, text="Shuffle", command=self.shuffle_callback,width=10)
        self.shffl_button.grid(row=0, column=0, sticky=tk.N+tk.S+tk.E+tk.W)
        
        self.skip_seen_flag = False
        self.skip_seen_button = tk.Button(frame_order, text="Skip Seen", command=self.skip_seen_callback, width=10)
        self.skip_seen_button.grid(row=0, column=1, sticky=tk.E+tk.W+tk.N+tk.S)

        self.only_seen_flag = False
        self.only_seen_button = tk.Button(frame_order, text="Only Seen", command=self.only_seen_callback,width=10)
        self.only_seen_button.grid(row=0, column=2, sticky=tk.E+tk.W+tk.N+tk.S)
        
        self.only_difficult_flag = False
        self.only_difficult_button = tk.Button(frame_order, text="Only Difficult", command=self.only_difficult_callback,width=15)
        self.only_difficult_button.grid(row=0, column=3, sticky=tk.E+tk.W+tk.N+tk.S)
        
        about_button = tk.Button(self,text='About',command=self.about_callback)
        about_button.grid(row=0, column=width-1,sticky=tk.N+tk.E)
        
        img_path = self.dbm.get_frame_path()
        image_raw = Image.open(img_path)
        img = ImageTk.PhotoImage(image_raw)
        self.img_label = ttk.Label(self, image=img,borderwidth=0,compound="center") #,highlightthickness = 0
        
        self.img_label.configure(image=img,anchor="center")
        self.img_label.image = img
        self.img_label.grid(row=2, column=0,columnspan=width, sticky=tk.N+tk.E+tk.W+tk.S,padx=0,pady=0)
        # image_raw = ImageOps.fit(image_raw,new_size, Image.ANTIALIAS)
        # print(new_size)
        
        img = ImageTk.PhotoImage(Image.open(img_path))#.resize(self.imsize))
        ##
        self.img_label = ttk.Label(self, image=img,borderwidth=0,compound="center") #,highlightthickness = 0
        self.img_label.grid(row=2, column=0,columnspan=width, sticky=tk.N+tk.E+tk.W+tk.S,padx=0,pady=0)
        self.img_label.image = img
        
        self.img_label.update()

        
        
        #Annotation panel
        self.frame_annot = ttk.Frame(self, borderwidth=10)
        self.frame_annot.grid(row=3, column=0, columnspan=width-2,sticky=tk.E+tk.W+tk.N+tk.S,padx=10,pady=20)
        
        self.entries = [ttk.Checkbutton(self.frame_annot,text=str(i),width=0.5) for i in range(1,4)]
        [self.entries[i].grid(row=0, column=i, sticky=tk.E+tk.W+tk.N+tk.S) for i in range(3)]        
        self.ok_button = ttk.Button(self.frame_annot, width=5,command=self.ok_callback, text='OK')
        self.ok_button.grid(row=0, column=3, sticky=tk.E+tk.W+tk.N+tk.S)
    
        
#         # Comment
        frame_comment = ttk.Frame(self, borderwidth=0)
        frame_comment.grid(row=4, column=0, columnspan=width-2,sticky=tk.E+tk.W+tk.N+tk.S,padx=10)
        
        comment_lbl = ttk.Label(frame_comment, text='Comment')
        comment_lbl.grid(row=0, column=0,sticky=tk.W)
        
        self.comment_line = tk.StringVar()
        comment = self.dbm.get_comment()
        self.comment_line.set(comment)
        self.comment_entry = tk.Entry(frame_comment, width = 35, textvariable=self.comment_line)
        self.comment_entry.grid(row=0, column=1,sticky=tk.W)
        
        
        # checkbox panel
        chk_frame = ttk.Frame(self, borderwidth=0,width=21)
        chk_frame.grid(row=3, column = width-2, rowspan=2,columnspan=2,sticky=tk.E,padx=10,pady=10)
        
        self.artifactChk = ttk.Checkbutton(chk_frame, text='artifact',width=21,command=self.clicked_artifactChk)
        self.artifactChk.grid(row=0, column = 0,sticky=tk.N)
        self.roi_not_seenChk = ttk.Checkbutton(chk_frame, text='ROI not visible',width=21,command=self.clicked_roi_not_seenChk)
        self.roi_not_seenChk.grid(row=1, column = 0,sticky=tk.N)
        self.roi_visible_partiallyChk = ttk.Checkbutton(chk_frame, text='ROI visible partially',width=21,command=self.clicked_roi_visible_partiallyChk)
        self.roi_visible_partiallyChk.grid(row=2, column = 0,sticky=tk.N)
        self.instrChk = ttk.Checkbutton(chk_frame, text='instrument in ROI',width=21,command=self.clicked_instrChk)
        self.instrChk.grid(row=3, column = 0,sticky=tk.N)
        self.diffChk = ttk.Checkbutton(chk_frame, text='difficult to review',width=21,command=self.clicked_diffChk)
        self.diffChk.grid(row=4, column = 0,sticky=tk.N)
        self.oobChk = ttk.Checkbutton(chk_frame, text='out-of-body',width=21,command=self.clicked_oobChk)
        self.oobChk.grid(row=5, column = 0,sticky=tk.N)
        self.post_viewChk = ttk.Checkbutton(chk_frame, text='posterior view',width=21,command=self.clicked_post_viewChk)
        self.post_viewChk.grid(row=6, column = 0,sticky=tk.N)
        self.anatomical_variationChk = ttk.Checkbutton(chk_frame, text='anatomical variation',width=21,command=self.clicked_anatomical_variationChk)
        self.anatomical_variationChk.grid(row=7, column = 0,sticky=tk.N)
        self.seenChk = ttk.Checkbutton(chk_frame, text='seen',width=21,command=self.clicked_seenChk)
        self.seenChk.grid(row=8, column = 0,sticky=tk.N)
        self.read_flags()
        self.show_label()
        
#         ######################################################        
        # Navigataion panel
        nav_frame = ttk.Frame(self, borderwidth=0)
        nav_frame.grid(row=5, column=0, columnspan=width,sticky=tk.S)#+tk.S)
        
        self.prev_button = ttk.Button(nav_frame, text="Prev",command=self.prev_callback)
        self.prev_button.grid(row=0, column=0, columnspan=1,sticky=tk.E+tk.W+tk.N+tk.S,padx=2)
        
        self.next_button = ttk.Button(nav_frame, text="Next", command=self.next_callback)
        self.next_button.grid(row=0, column=1, columnspan=1,sticky=tk.E+tk.W+tk.N+tk.S,padx=2)
        
        
        r = 0.8
        logo_img1 = ImageTk.PhotoImage(Image.open(self.logo1_path).resize([int(150*r), int(57*r)]))
        logo_label1 = tk.Label(self, image=logo_img1)
        logo_label1.image = logo_img1
        logo_label1.grid(row=6, column=0, columnspan=2,sticky=tk.W+tk.S, padx=10, pady=10)

        
        right_logo_frame = ttk.Frame(self, borderwidth=0)
        right_logo_frame.grid(row=6, column = width-1,  sticky=tk.E)
        
        logo_img3 = ImageTk.PhotoImage(Image.open(self.logo3_path).resize([int(70*r), int(70*r)]))
        logo_label3 = tk.Label(right_logo_frame, image=logo_img3)
        logo_label3.image = logo_img3
        logo_label3.grid(row=0, column=0, sticky=tk.E+tk.S, padx=10, pady=10)
        
        logo_img2 = ImageTk.PhotoImage(Image.open(self.logo2_path).resize([int(160*r), int(74*r)]))
        logo_label2 = ttk.Label(right_logo_frame, image=logo_img2)
        logo_label2.image = logo_img2
        logo_label2.grid(row=0, column=1, sticky=tk.W+tk.S, padx=10, pady=10)
        
    
    def shuffle_callback(self):
        if not self.shuffle_flag: #turn shuffling on
            self.shuffle_flag = True
            self.shffl_button.configure(text='_Shuffle_')
        else:
            self.shuffle_flag = False
            
            self.shffl_button.config(text='Shuffle')
        self.dbm.toggle_shuffle(self.shuffle_flag)
        self.update_frame()
    
    def only_seen_callback(self):
        if self.skip_seen_flag:
            return
        
        if not self.only_seen_flag: 
            self.only_seen_flag = True
            self.only_seen_button.configure(text='_Only Seen_')
        else:
            self.only_seen_flag = False
            
            self.only_seen_button.config(text='Only Seen')
        self.dbm.toggle_only_seen(self.only_seen_flag)
    
    def only_difficult_callback(self):
        if not self.only_difficult_flag: 
            self.only_difficult_flag = True
            self.only_difficult_button.configure(text='_Only Difficult_')
        else:
            self.only_difficult_flag = False
            
            self.only_difficult_button.config(text='Only Difficult')
        self.dbm.toggle_only_difficult(self.only_difficult_flag)
        
    def skip_seen_callback(self):
        if self.only_seen_flag:
            return
        
        if not self.skip_seen_flag:
            
            self.skip_seen_flag = True
            self.skip_seen_button.configure(text='_Skip Seen_')
        else:
            self.skip_seen_flag = False
            
            self.skip_seen_button.config(text='Skip Seen')
        self.dbm.toggle_skip_seen(self.skip_seen_flag)
       
    def about_callback(self):
        messagebox.showinfo(title="About",message="""This application was developed by Research Group CAMMA, University of Strasbourg (http://camma.u-strasbg.fr). \nThis code is available for non-commercial scientific research purposes as defined in the CC BY-NC-SA 4.0. By downloading and using this code you agree to the terms in the LICENSE. Third-party codes are subject to their respective licenses.""")

    
    def update_frame(self):
        img_path = self.dbm.get_frame_path()
        
        # self.img_frame.update()
        new_size = [self.img_label.winfo_width(),self.img_label.winfo_height()]
        image_raw = Image.open(img_path)
        
        image_raw = get_resized_img(image_raw, new_size)
        # image_raw = ImageOps.fit(image_raw,new_size, Image.ANTIALIAS)
        # print(new_size)
        
        img = ImageTk.PhotoImage(image_raw)
        self.img_label.configure(image=img,anchor="center")
        self.img_label.image = img
        
        fr = self.dbm.get_id()
        self.vid_id_line.set(str(fr[0]))
        self.frame_id_line.set(str(fr[1]))
        
        comment = self.dbm.get_comment()
        self.comment_line.set(comment)
        
        progress = self.dbm.get_progress()
        self.progress_line.set('  {} / {}'.format(*progress))
        
        self.read_flags()

        
        self.show_label()
        
    def maybe_save_comment(self):
        comment = self.comment_entry.get()
        
        if comment != self.dbm.get_comment():
            self.dbm.set_comment(comment)
    
    def goto_callback(self):
        self.maybe_save_comment()
        self.dbm.goto_frame(self.vid_id_entry.get(), self.frame_id_entry.get())
        self.update_frame()
        
    def openVid_callback(self):

        with open(self.config_path, 'r') as f:
            info = json.load(f)
            
        if 'videos_dir' not in info:
            videos_dir = tk.filedialog.askdirectory(title='Select folder containing videos')
    
            if len(videos_dir) != 0:
                info['videos_dir'] = videos_dir
                with open(self.config_path, 'w') as f:    
                    json.dump(info, f)

        videos_dir = info['videos_dir']
        
        fr = self.dbm.get_id()
        vid_id = str(fr[0])
        
        found_vid = glob1(videos_dir, vid_id + '*')
        
        try:
            assert(len(found_vid) <= 1)
        except:
            print('Error: Multiple files found ', found_vid)
            return -1
        
        try:
            assert(len(found_vid)==1)
            vidpath = os.path.join(videos_dir, found_vid[0])
            assert(os.path.exists(vidpath))
        except:
            print('File not found : ', os.path.join(videos_dir, vid_id+'*'))
            return -1
        
        vlc_path = ''
        if is_tool('vlc'):
            vlc_path = "vlc"
        elif 'vlc_path' in info:
            vlc_path = info['vlc_path']
			
        else:
            vlc_path = tk.filedialog.askopenfilename(title='Select path to VLC')
            if vlc_path != '':
                info['vlc_path'] = vlc_path
                with open(self.config_path, 'w') as f:    
                    json.dump(info, f)
        try:
            assert is_tool(vlc_path)
        except:
            print('ERROR: vlc not found {}'.format(vlc_path))
            return
        
        vidpath = str(Path(vidpath))
        vlc_path = str(Path(vlc_path))
        
        
        cam = cv2.VideoCapture(vidpath)
        fps = cam.get(cv2.CAP_PROP_FPS)
        
        seconds = int(fr[1] / fps)
        print(fps)
        
        print('INFO: Opening video ',vidpath)
        
        args = [which(vlc_path), "--start-time={}".format(seconds), vidpath]
        print(args)
        Popen(args)
 
    def next_callback(self):
        self.maybe_save_comment()
        self.dbm.next_frame()
        self.update_frame()
        
    def prev_callback(self):
        self.maybe_save_comment()
        self.dbm.prev_frame()
        self.update_frame()
    
    def read_flags(self):
        flags = self.dbm.get_flags()
        
        self.instrChk.state(['!alternate'])
        if flags['instr_in_roi']:
            self.instrChk.state(['!disabled','selected'])
        else:
            self.instrChk.state(['!selected',])
        

        self.diffChk.state(['!alternate'])
        if flags['difficult']:
            self.diffChk.state(['!disabled','selected'])
        else:
            self.diffChk.state(['!selected',])
            
        self.oobChk.state(['!alternate'])
        if flags['out_of_body']:
            self.oobChk.state(['!disabled','selected'])
        else:
            self.oobChk.state(['!selected',])
            
        self.seenChk.state(['!alternate'])
        if flags['seen']:
            self.seenChk.state(['!disabled','selected'])
        else:
            self.seenChk.state(['!selected',])
            
        self.post_viewChk.state(['!alternate'])
        if flags['post_view']:
            self.post_viewChk.state(['!disabled','selected'])
        else:
            self.post_viewChk.state(['!selected',])
            
        self.anatomical_variationChk.state(['!alternate'])
        if flags['anatomical_variation']:
            self.anatomical_variationChk.state(['!disabled','selected'])
        else:
            self.anatomical_variationChk.state(['!selected',])
        
        self.roi_not_seenChk.state(['!alternate'])
        
        if flags['roi_not_seen']:
            self.roi_not_seenChk.state(['!disabled','selected'])
        else:
            self.roi_not_seenChk.state(['!selected',])
            
        self.artifactChk.state(['!alternate'])
        if flags['artifact']:
            self.artifactChk.state(['!disabled','selected'])
        else:
            self.artifactChk.state(['!selected',])
            
        self.roi_visible_partiallyChk.state(['!alternate'])
        if flags['roi_visible_partially']:
            self.roi_visible_partiallyChk.state(['!disabled','selected'])
        else:
            self.roi_visible_partiallyChk.state(['!selected',])
        
    def clicked_instrChk(self):
        new_state = int(self.instrChk.instate(['selected']))
        self.dbm.set_instr_flag(new_state)
    
    def clicked_roi_not_seenChk(self):
        new_state = int(self.roi_not_seenChk.instate(['selected']))
        self.dbm.set_roi_not_seen_flag(new_state)
        
    def clicked_roi_visible_partiallyChk(self):
        new_state = int(self.roi_visible_partiallyChk.instate(['selected']))
        self.dbm.set_roi_visible_partially_flag(new_state)
        
    
    def clicked_artifactChk(self):
        new_state = int(self.artifactChk.instate(['selected']))
        self.dbm.set_artifact_flag(new_state)
        
    def clicked_diffChk(self):
        new_state = int(self.diffChk.instate(['selected']))
        self.dbm.set_diff_flag(new_state)
    
    def clicked_oobChk(self):
        new_state = int(self.oobChk.instate(['selected']))
        self.dbm.set_oob_flag(new_state)
        
    def clicked_seenChk(self):
        new_state = int(self.seenChk.instate(['selected']))
        self.dbm.set_seen_flag(new_state)
    
    def clicked_post_viewChk(self):
        new_state = int(self.post_viewChk.instate(['selected']))
        self.dbm.set_post_view_flag(new_state)
        
    def clicked_anatomical_variationChk(self):
        new_state = int(self.anatomical_variationChk.instate(['selected']))
        self.dbm.set_anatomical_variation_flag(new_state)
    
    def show_label(self):
#        self.show_label_btn.configure(text="Hide Label")
        
        [chk.state(['!alternate']) for chk in self.entries]
        
        labels = self.dbm.get_labels()
        
        for i,l in enumerate(labels):
            if l:
                self.entries[i].state(['!disabled','selected'])
            else:
                self.entries[i].state(['!disabled','!selected'])
        
    
    def hide_label(self):
        self.show_label_btn.configure(text="Show Label")
            
        [chk.state(['!selected']) for chk in self.entries]
        [chk.state(['alternate']) for chk in self.entries]
    
    def ok_callback(self):

        new_labels = [int(chk.instate(['selected'])) for chk in self.entries]
        self.dbm.set_labels(new_labels)
        
        self.seenChk.state(['!disabled','selected'])
        self.clicked_seenChk()
        
    def leftKey(self, event):
        if not self.text_editing_mode:
            self.prev_button.invoke()
    
    def rightKey(self, event):
        if not self.text_editing_mode:
            self.next_button.invoke()
    
    def toggleCheckbox(self, chkbx):
        state = chkbx.instate(['selected'])
        
        if not state:
            chkbx.state(['!disabled','selected'])
        else:
            chkbx.state(['!selected'])
        
        
    def upKey(self, event):
        self.toggleCheckbox(self.seenChk)
        
        self.clicked_seenChk()
        
    def returnKey(self,event):
        if self.text_editing_mode:
            return
        self.ok_button.state(['pressed'])
        self.ok_button.invoke()
        self.ok_button.after(100, lambda : self.ok_button.state(['!pressed']))
        
    def oneKey(self, event):
        self.toggleCheckbox(self.entries[0])
        
    def twoKey(self, event):
        self.toggleCheckbox(self.entries[1])
        
    def threeKey(self, event):
        self.toggleCheckbox(self.entries[2])

    def ctrl_aKey(self, event):
        self.toggleCheckbox(self.artifactChk)
        self.clicked_artifactChk()
        
    def ctrl_nKey(self, event):
        self.toggleCheckbox(self.roi_not_seenChk)
        self.clicked_roi_not_seenChk()
    
    def ctrl_rKey(self, event):
        self.toggleCheckbox(self.roi_visible_partiallyChk)
        self.clicked_roi_visible_partiallyChk()

    def ctrl_iKey(self, event):
        self.toggleCheckbox(self.instrChk)
        self.clicked_instrChk()
        
    def ctrl_dKey(self, event):
        self.toggleCheckbox(self.diffChk)
        self.clicked_diffChk()
        
    def ctrl_oKey(self, event):
        self.toggleCheckbox(self.oobChk)
        self.clicked_oobChk()
        
    def ctrl_pKey(self, event):
        self.toggleCheckbox(self.post_viewChk)
        self.clicked_post_viewChk()
                
    def ctrl_vKey(self, event):
        if self.text_editing_mode:
            return
        self.toggleCheckbox(self.anatomical_variationChk)
        self.clicked_anatomical_variationChk()
            
    # <Control+a>'  : Toggle artifact
    # <Control+n>'  : Toggle ROI not visible
    # <Control+r>'  : Toggle ROI visible partially 
    # <Control+i>'  : Toggle instrument in roi
    # <Control+d>'  : Toggle difficult to review
    # <Control+o>'  : Toggle out of body
    # <Control+p>'  : Toggle posterior view
    # <Control+v>'  : Toggle anatomical variation
