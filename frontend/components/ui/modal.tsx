import React from 'react';
import { Dialog, DialogOverlay, DialogContent } from '@reach/dialog';
import '@reach/dialog/styles.css';

interface ModalProps {
    isOpen: boolean;
    onClose: () => void;
    children: React.ReactNode;
    className?: string;
}


const Modal: React.FC<ModalProps> = ({ isOpen, onClose, children, className }) => {
    return (
        <Dialog isOpen={isOpen} onDismiss={onClose} aria-label="File Explorer Modal" className={className}>
            <DialogOverlay>
                <DialogContent>
                    <button className="close-button" onClick={onClose}>
                        <span aria-hidden>×</span>
                    </button>
                    {children}
                </DialogContent>
            </DialogOverlay>
        </Dialog>
    );
};

export default Modal;