from data.evaluate.voc_eval import voc_evaluationimport torchclass base_val(object):    def __init__(self,img_info,gt_info,classes):        self.img_info = img_info        self.gt_info = gt_info        self.classes = classes    def get_img_info(self,x):        return self.img_info[x]    def get_groundtruth(self,x):        return self.gt_info[x]    def map_class_id_to_class_name(self,x):        return self.classes[x]def training_eval(model,valload,classes,device):    model.eval()    img_info = dict()    gt_info = dict()    predictions = []    print("eval {} total img {}".format(len(classes),len(valload.dataset)))    with torch.no_grad():        for img,target,meta in valload:            bs = img.shape[0]            img = img.to(device)            batch_box = model(img)            assert len(batch_box) == bs,(len(batch_box))            for i in range(bs):                fileID = meta[i]['fileID']                img_info[fileID] = dict(width=meta[i]['img_width'],height=meta[i]['img_height'])                gt_info[fileID] = meta[i]['boxlist']                box = batch_box[i]                #TODO padding test                box.resize((meta[i]['img_width'],meta[i]['img_height']))                predictions.append([fileID,box])        gt_sets = base_val(img_info,gt_info,classes)    model.train()    result = voc_evaluation(gt_sets,predictions,'./',box_only=True)    for i,value in enumerate(result['ap']):        result[classes[i]] = value    del result['ap']    return resultif __name__ == "__main__":    from data.build import make_dist_voc_loader    from cfg.voc import cfg    from yolo import create_yolov1    import os    train_cfg = cfg['train_cfg']    model_cfg = cfg['model_cfg']    model_name = model_cfg['model_type']    epochs = train_cfg['epochs']    classes = train_cfg['classes']    lr = train_cfg['lr']    bs = train_cfg['batch_size']    device = train_cfg['device']    out_dir = train_cfg['out_dir']    resume = train_cfg['resume']    use_sgd = train_cfg['use_sgd']    scale = train_cfg['scale']    mile = train_cfg['milestone']    gamma = train_cfg['gamma']    train_root = train_cfg['dataroot']    patch_size = train_cfg['patch_size']    out_dir = out_dir + '/' + model_name    model = create_yolov1(model_cfg)    checkpoint = torch.load('{}/best_model.pth'.format(out_dir))['model']    data_dict = {k.replace('module.', ''): v for k, v in checkpoint.items()}    model.load_state_dict(data_dict, strict=True)    model.eval()    model.cuda()    valloader = make_dist_voc_loader(os.path.join(train_root,'VOC2007_test.txt'),img_size=[(448,448)],                                 batch_size=16,                                 train=False,rank=0                                )    training_eval(model, valloader, classes, device)