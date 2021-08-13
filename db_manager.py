#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""   
(c) Research Group CAMMA, University of Strasbourg, France
Website: http://camma.u-strasbg.fr
Code author: Armine Vardazaryan
"""

import pandas as pd
import numpy as np
import os
import pickle
from glob import glob1

header = {
        'video_id', 
        'frame_id', 
        'frame_id_int',
        'instr_in_roi', 
        'comment', 
        'difficult', 
        'out_of_body',
        'seen', 
        'post_view', 
        'cvs_cri_1', 
        'cvs_cri_2', 
        'cvs_cri_3', 
        'anatomical_variation', 
        'roi_not_seen', 
        'artifact',
        'roi_visible_partially'
        }

def load_from_dataset(p):
    d = []
    for root, dirs, files in os.walk(p):
        if root==p:
            continue
        vidname = os.path.basename(root)

        for framename in files:
            if not framename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            frame_id, fileformat = framename.split('.')
            frame_id_int = int(frame_id)
            
            d.append([vidname, frame_id, frame_id_int]) 
    
    d = np.vstack(d) 
    
    df = pd.DataFrame(columns=header)
    
    df['video_id'] = d[:,0]
    df['video_id'] = df['video_id'].astype(str)
    
    df['frame_id'] = d[:,1]
    df['frame_id'] = df['frame_id'].astype(str)
    
    df['frame_id_int'] = d[:,2]
    df['frame_id_int'] = df['frame_id_int'].astype(int)
    
    cols = ['video_id', 'frame_id', 'frame_id_int', 'comment']
    for c in cols:
        df[c].fillna("", inplace=True)
    
    
    cols = ['instr_in_roi', 'difficult', 'out_of_body', 'seen', 'post_view', 
            'cvs_cri_1', 'cvs_cri_2', 'cvs_cri_3', 'anatomical_variation',
            'roi_not_seen', 'artifact','roi_visible_partially']
    for c in cols:
        df[c].fillna(0, inplace=True)
    
    df = df.sort_values(['video_id','frame_id_int'])
    df = df.reset_index(drop=True)
    
    return df, fileformat

def find_file_extension(p):
    """ takes a path with a partial file name. Returns full path of file """
    dirpath = os.path.dirname(p)
    filename = os.path.basename(p)
    
    files = glob1(dirpath, '*.png')
    files.extend(glob1(dirpath, '*.jpg'))
    files.extend(glob1(dirpath, '*.jpeg'))
    
    found_filename = [f for f in files if filename in f]
    assert(len(found_filename) > 0)
    
    extension = found_filename[0].split('.')[1]
    return extension

class DB_Manager:

    def __init__(self, frames_path, annotation_path):
        self.frames_path = frames_path
        
        self.annotation_path = annotation_path
        
        try:
            self.database = pd.read_pickle(self.annotation_path)
            
            self.fileformat = find_file_extension(os.path.join(self.frames_path, self.database.iloc[0]['video_id'], self.database.iloc[0]['frame_id']))
            
        except (OSError, IOError) as e:
            self.database, self.fileformat = load_from_dataset(self.frames_path)
            self.save_database()
            
        assert(len(self.database) > 0)
        
        
        self._current_frame_idx = 0
        self.n_frames = len(self.database)

        self.shuffled_indices = np.arange(self.n_frames)
        np.random.seed(42)
        np.random.shuffle(self.shuffled_indices)
        
        self.shuffled = False
        self.skip_seen = False
        self.only_seen = False
        self.only_difficult = False
        
        #load history
        self.history_path = os.path.join(os.path.dirname(os.path.abspath(self.annotation_path)), 'history.pickle')
        if os.path.exists(self.history_path):
            with open(self.history_path, 'rb') as handle:
                self.history = pickle.load(handle)
        else:
            self.history = []
        
        
    def save_history(self, before_frame, after_frame):
        
        if np.all(before_frame == after_frame):
            return
        
        self.history.append((list(before_frame), list(after_frame)))
        
        with open(self.history_path, 'wb') as handle:
            pickle.dump(self.history, handle)
    
    def save_database(self):
        self.database.to_pickle(self.annotation_path)#, index=False)
        self.database.to_csv(self.annotation_path.split('.')[0]+'.csv')
        
    def get_frame(self):
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx
        return self.database.iloc[idx]
    
    def get_id(self):
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx
            
        return (self.database.iloc[idx]['video_id'], self.database.iloc[idx]['frame_id_int'])
    
    def get_comment(self):
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx
            
        comment = self.database.iloc[idx]['comment']
        if not comment:
            return ''
        return comment
    
    def get_progress(self):
        return ((self._current_frame_idx + 1), self.n_frames)
    
    def get_frame_path(self):
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx
        vid_dir = self.database.iloc[idx]['video_id']
        
        file_name = self.database.iloc[idx]['frame_id'] +'.'+self.fileformat
        return os.path.join(self.frames_path, vid_dir, file_name)
        
        
    def next_frame(self):
        counter = 0
        while True:
            self._current_frame_idx += 1
            self._current_frame_idx %= self.n_frames
            
            if self.shuffled:
                idx = self.shuffled_indices[self._current_frame_idx]
            else:
                idx = self._current_frame_idx
                    
            seen = self.database.loc[idx, 'seen']
            difficult = self.database.loc[idx, 'difficult']
            
            if not (self.skip_seen and seen) \
                and not (self.only_difficult and not difficult) \
                and not (self.only_seen and not seen):
                break
            
            counter += 1
            if counter >= self.n_frames:
                break
            
        return self.database.iloc[idx]
            
    def prev_frame(self):
        counter = 0
        while True:            
            self._current_frame_idx -= 1
            self._current_frame_idx %= self.n_frames
            
            if self.shuffled:
                idx = self.shuffled_indices[self._current_frame_idx]
            else:
                idx = self._current_frame_idx
                    
            seen = self.database.loc[idx, 'seen']
            difficult = self.database.loc[idx, 'difficult']
            
            if not (self.skip_seen and seen) \
                and not (self.only_difficult and not difficult) \
                and not (self.only_seen and not seen):
                break
            
            counter += 1
            if counter >= self.n_frames:
                break
            
        return self.database.iloc[idx]
    
    def get_labels(self):
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx
            
        c1 = self.database.iloc[idx]['cvs_cri_1']
        c2 = self.database.iloc[idx]['cvs_cri_2']
        c3 = self.database.iloc[idx]['cvs_cri_3']
        
        return [c1, c2, c3]
    
    def get_flags(self):

        return self.get_frame()
    
    def update_value(self, field_name, new_value):
        old_frame_data = self.get_frame().copy()
        
        if self.shuffled:
            idx = self.shuffled_indices[self._current_frame_idx]
        else:
            idx = self._current_frame_idx

        self.database.loc[idx, field_name] = new_value
        
        new_frame_data = self.get_frame().copy()
        
        self.save_history(old_frame_data, new_frame_data)
        
        self.save_database()
        
    def set_labels(self, new_labels):
        if len(new_labels) != 3:
            return
        
        self.update_value('cvs_cri_1', new_labels[0])
        self.update_value('cvs_cri_2', new_labels[1])
        self.update_value('cvs_cri_3', new_labels[2])
        
    def set_instr_flag(self, new_state):
        self.update_value('instr_in_roi', new_state)
        
    def set_diff_flag(self, new_state):
        self.update_value('difficult', new_state)
        
    def set_oob_flag(self, new_state):
        
        self.update_value('out_of_body', new_state)
        
    def set_seen_flag(self, new_state):
        self.update_value('seen', new_state)
    
    def set_post_view_flag(self, new_state):
        self.update_value('post_view', new_state)
        
    def set_roi_not_seen_flag(self, new_state):
        self.update_value('roi_not_seen', new_state)
        
    def set_artifact_flag(self, new_state):
        self.update_value('artifact', new_state)
        
    def set_roi_visible_partially_flag(self, new_state):
        self.update_value('roi_visible_partially', new_state)
        
        
    def set_anatomical_variation_flag(self, new_state):
        self.update_value('anatomical_variation', new_state)
        
    def set_comment(self, comment):
        
        self.update_value('comment', comment)
    
    def goto_frame(self, vid_id, frame_id):
        
        try:
            frame_id_int = int(frame_id)
        except:
            print('ERROR: frame id should only contain numbers ',frame_id)
            return 
        
        
        found_idx = np.where((self.database['frame_id_int']==frame_id_int) & (self.database['video_id']==vid_id))[0]
        
        if len(found_idx) == 0:
            return
        
        found_idx = found_idx[0]
        
        if self.shuffled:
            self._current_frame_idx = np.where(self.shuffled_indices==found_idx)[0][0]
        else:
            self._current_frame_idx = found_idx

    def toggle_shuffle(self, shuffle=False):
        self.shuffled = shuffle
        
    def toggle_skip_seen(self, skip=False):
        self.skip_seen = skip
        
    def toggle_only_seen(self, only_seen=False):
        self.only_seen = only_seen
        
    def toggle_only_difficult(self, only_difficult=False):
        self.only_difficult = only_difficult
      
