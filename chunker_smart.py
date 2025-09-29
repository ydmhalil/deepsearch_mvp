from typing import List, Dict, Optional, Tuple
import re
import math
import os


class SmartChunker:
    """Belge tipine göre adaptive chunking sistemi"""
    
    def __init__(self):
        self.default_chunk_size = 800
        self.default_overlap = 160
        
        # Belge tipi bazlı chunk stratejileri
        self.strategies = {
            '.txt': self._chunk_text_file,
            '.pdf': self._chunk_pdf_content, 
            '.docx': self._chunk_docx_content,
            '.pptx': self._chunk_pptx_content,
            '.xlsx': self._chunk_xlsx_content
        }
    
    def chunk_document(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """Ana chunking fonksiyonu - dosya tipine göre strateji seçer"""
        if not text or not text.strip():
            return []
        
        file_ext = os.path.splitext(file_path)[1].lower()
        strategy = self.strategies.get(file_ext, self._chunk_text_file)
        
        chunks = strategy(text, file_path, **kwargs)
        
        # Her chunk'a genel metadata ekle
        for i, chunk in enumerate(chunks):
            chunk['meta'].update({
                'file_path': file_path,
                'file_type': file_ext,
                'file_name': os.path.basename(file_path),
                'chunk_index': i,
                'total_chunks': len(chunks)
            })
        
        return chunks
    
    def _chunk_text_file(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """TXT dosyalar için chunking - paragraf bazlı"""
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            para_text = paragraph.strip()
            if not para_text:
                continue
                
            para_tokens = len(para_text.split())
            
            # Eğer paragraf tek başına çok büyükse böl
            if para_tokens > self.default_chunk_size:
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_id, 'paragraph_group'))
                    chunk_id += 1
                    current_chunk = ""
                    current_tokens = 0
                
                # Büyük paragrafı alt parçalara böl
                sub_chunks = self._split_large_paragraph(para_text, chunk_id, para_idx)
                chunks.extend(sub_chunks)
                chunk_id += len(sub_chunks)
                
            elif current_tokens + para_tokens > self.default_chunk_size:
                # Mevcut chunk'ı kaydet
                if current_chunk:
                    chunks.append(self._create_chunk(current_chunk, chunk_id, 'paragraph_group'))
                    chunk_id += 1
                
                current_chunk = para_text
                current_tokens = para_tokens
                
            else:
                # Paragrafi mevcut chunk'a ekle
                if current_chunk:
                    current_chunk += "\n\n" + para_text
                else:
                    current_chunk = para_text
                current_tokens += para_tokens
        
        # Son chunk'ı kaydet
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_id, 'paragraph_group'))
        
        return chunks
    
    def _chunk_pdf_content(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """PDF için chunking - sayfa bazlı yaklaşım"""
        chunks = []
        
        # PDF text'inde sayfa belirteci varsa kullan
        if '[OCR]' in text:
            # OCR içeriği olan PDF'lerde özel işlem
            return self._chunk_ocr_pdf(text, file_path)
        
        # Normal PDF chunking - paragraf bazlı ama daha küçük chunks
        return self._chunk_text_with_sentences(text, chunk_size=600, chunk_type='pdf_section')
    
    def _chunk_docx_content(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """DOCX için chunking - paragraf bazlı"""
        return self._chunk_text_file(text, file_path, **kwargs)
    
    def _chunk_pptx_content(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """PowerPoint için chunking - slide bazlı"""
        chunks = []
        
        # Slide içeriğini ayırmaya çalış (basit yaklaşım)
        sections = text.split('\n\n')
        
        current_slide = ""
        slide_num = 1
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Eğer section çok kısaysa önceki slide'a ekle
            if len(section.split()) < 20 and current_slide:
                current_slide += "\n\n" + section
            else:
                # Önceki slide'ı kaydet
                if current_slide:
                    chunks.append({
                        'text': current_slide,
                        'meta': {
                            'tokens': len(current_slide.split()),
                            'chunk_type': f'slide_{slide_num}',
                            'structure_type': 'presentation_slide'
                        }
                    })
                    slide_num += 1
                
                current_slide = section
        
        # Son slide'ı kaydet
        if current_slide:
            chunks.append({
                'text': current_slide,
                'meta': {
                    'tokens': len(current_slide.split()),
                    'chunk_type': f'slide_{slide_num}',
                    'structure_type': 'presentation_slide'
                }
            })
        
        return chunks
    
    def _chunk_xlsx_content(self, text: str, file_path: str, **kwargs) -> List[Dict]:
        """Excel için chunking - sheet bazlı"""
        chunks = []
        
        # Sheet başlıklarını tanı
        sheet_sections = re.split(r'Sheet:\s+(.+?)\n', text)
        
        current_sheet = ""
        sheet_name = "Unknown"
        
        for i, section in enumerate(sheet_sections):
            if i == 0:
                continue  # İlk bölüm genelde boş
                
            if i % 2 == 1:  # Sheet adı
                if current_sheet:
                    chunks.append(self._create_sheet_chunk(current_sheet, sheet_name))
                sheet_name = section.strip()
                current_sheet = ""
            else:  # Sheet içeriği
                current_sheet = section.strip()
        
        # Son sheet'i kaydet
        if current_sheet:
            chunks.append(self._create_sheet_chunk(current_sheet, sheet_name))
        
        return chunks
    
    def _chunk_text_with_sentences(self, text: str, chunk_size: int = 800, chunk_type: str = 'text_section') -> List[Dict]:
        """Cümle sınırlarına saygılı chunking"""
        chunks = []
        
        # Cümleleri ayır
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_tokens = len(sentence.split())
            
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                # Chunk'ı kaydet
                chunks.append(self._create_chunk(current_chunk, chunk_id, chunk_type))
                chunk_id += 1
                current_chunk = sentence
                current_tokens = sentence_tokens
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                current_tokens += sentence_tokens
        
        # Son chunk'ı kaydet
        if current_chunk:
            chunks.append(self._create_chunk(current_chunk, chunk_id, chunk_type))
        
        return chunks
    
    def _split_large_paragraph(self, paragraph: str, base_chunk_id: int, para_idx: int) -> List[Dict]:
        """Büyük paragrafı alt-chunklara böl"""
        return self._chunk_text_with_sentences(paragraph, chunk_type=f'large_paragraph_{para_idx}')
    
    def _create_chunk(self, text: str, chunk_id: int, chunk_type: str) -> Dict:
        """Standart chunk objesi oluştur"""
        return {
            'text': text,
            'meta': {
                'tokens': len(text.split()),
                'chunk_id': chunk_id,
                'chunk_type': chunk_type,
                'structure_type': 'text_based'
            }
        }
    
    def _create_sheet_chunk(self, content: str, sheet_name: str) -> Dict:
        """Excel sheet chunk'ı oluştur"""
        return {
            'text': content,
            'meta': {
                'tokens': len(content.split()),
                'chunk_type': f'sheet_{sheet_name}',
                'sheet_name': sheet_name,
                'structure_type': 'spreadsheet_sheet'
            }
        }
    
    def _chunk_ocr_pdf(self, text: str, file_path: str) -> List[Dict]:
        """OCR içeren PDF'ler için özel chunking"""
        chunks = []
        
        # OCR ve normal metni ayır
        sections = text.split('[OCR]')
        
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
                
            chunk_type = 'ocr_content' if i > 0 else 'pdf_text'
            section_chunks = self._chunk_text_with_sentences(section, chunk_type=chunk_type)
            chunks.extend(section_chunks)
        
        return chunks


# Backward compatibility için eski fonksiyon
def chunk_text(text: str, chunk_size: int = 800, overlap: int = 160, file_path: str = None) -> List[Dict]:
    """Eski API ile uyumluluk - yeni SmartChunker kullanır"""
    chunker = SmartChunker()
    
    if file_path:
        return chunker.chunk_document(text, file_path)
    else:
        # Eski davranış - basit text chunking
        return chunker._chunk_text_with_sentences(text)