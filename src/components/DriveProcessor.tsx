import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import * as XLSX from 'xlsx';

const API_BASE_URL = import.meta.env.VITE_API_URL || (import.meta.env.PROD ? '' : 'http://localhost:8000');

const DriveProcessor = () => {
    const [file, setFile] = useState<File | null>(null);
    const [rowCount, setRowCount] = useState(0);
    const [mes, setMes] = useState('diciembre');
    const [status, setStatus] = useState<'upload' | 'processing' | 'success' | 'failed'>('upload');
    const [showAlert, setShowAlert] = useState(false);
    const [progress, setProgress] = useState({ current: 0, total: 0, lastItem: '', percent: 0 });
    const [results, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        const handleBeforeUnload = (e: BeforeUnloadEvent) => {
            if (status === 'processing') {
                e.preventDefault();
                e.returnValue = ''; // Requerido por Chrome
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [status]);

    const handleFile = async (e: React.ChangeEvent<HTMLInputElement> | React.DragEvent) => {
        setError(null);
        let selectedFile: File | null = null;
        if ('files' in e.target && e.target.files) {
            selectedFile = e.target.files[0];
        } else if ('dataTransfer' in e && e.dataTransfer.files) {
            selectedFile = e.dataTransfer.files[0];
        }

        if (selectedFile && selectedFile.name.match(/\.(xlsx|xls)$/)) {
            setFile(selectedFile);
            const data = await selectedFile.arrayBuffer();
            const workbook = XLSX.read(data, { type: 'array' });
            const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
            const rows = XLSX.utils.sheet_to_json(firstSheet);
            setRowCount(rows.length);
        }
    };

    const startProcessing = async () => {
        if (!file) return;
        setStatus('processing');
        setError(null);
        
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mes', mes);

        try {
            const response = await fetch(`${API_BASE_URL}/api/process/`, { method: 'POST', body: formData });
            if (!response.ok) throw new Error('Error al iniciar el procesamiento');
            const data = await response.json();
            pollStatus(data.task_id);
        } catch (err) {
            setError('No se pudo conectar con el servidor');
            setStatus('failed');
        }
    };

    const pollStatus = (taskId: string) => {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`${API_BASE_URL}/api/status/${taskId}`);
                if (!res.ok) throw new Error('Error al consultar el estado');
                const data = await res.json();
                
                const percent = data.total > 0 ? Math.round((data.current / data.total) * 100) : 0;
                setProgress({ current: data.current, total: data.total, lastItem: data.last_item, percent });

                if (data.status === 'completed') {
                    clearInterval(interval);
                    setResult({
                        ...data,
                        zip_url: `${API_BASE_URL}/api/download/${taskId}`
                    });
                    setStatus('success');
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    setError(data.errors?.[0] || 'La tarea falló en el servidor');
                    setStatus('failed');
                }
            } catch (err) {
                clearInterval(interval);
                setError('Se perdió la conexión con el servidor');
                setStatus('failed');
            }
        }, 1000);
    };

    return (
        <div className="relative">
            <AnimatePresence mode="wait">
                {status === 'upload' && (
                    <motion.div
                        key="upload"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.98 }}
                        transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
                        className="space-y-10"
                    >
                        {/* Alert Modal */}
                        <AnimatePresence>
                            {showAlert && (
                                <motion.div
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="fixed inset-0 z-[60] flex items-center justify-center px-6"
                                >
                                    <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setShowAlert(false)}></div>
                                    <motion.div
                                        initial={{ scale: 0.9, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0.9, opacity: 0 }}
                                        className="bg-white rounded-[28px] shadow-[0_20px_60px_rgba(0,0,0,0.15)] p-8 max-w-[400px] w-full relative z-10 text-center"
                                    >
                                        <div className="w-16 h-16 bg-[#FFF9E6] rounded-full flex items-center justify-center mx-auto mb-6 text-[#FFB800]">
                                            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                            </svg>
                                        </div>
                                        <h3 className="text-xl font-semibold mb-3">Recordatorio importante</h3>
                                        <p className="text-[#86868B] mb-8">
                                            Para que el proceso funcione correctamente, asegúrate de que todos los archivos de Google Drive tengan el <b>acceso público</b> activado (Cualquier persona con el enlace).
                                        </p>
                                        <div className="space-y-3">
                                            <button 
                                                onClick={() => {
                                                    setShowAlert(false);
                                                    startProcessing();
                                                }}
                                                className="w-full bg-[#0071E3] text-white font-semibold py-3.5 rounded-xl hover:bg-[#0077ED] transition-all"
                                            >
                                                Entendido, procesar
                                            </button>
                                            <button 
                                                onClick={() => setShowAlert(false)}
                                                className="w-full bg-transparent text-[#0071E3] font-medium py-2 hover:underline transition-all"
                                            >
                                                Revisar archivos
                                            </button>
                                        </div>
                                    </motion.div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        {/* Drag & Drop */}
                        <div 
                            onClick={() => fileInputRef.current?.click()}
                            onDragOver={(e) => e.preventDefault()}
                            onDrop={(e) => { e.preventDefault(); handleFile(e); }}
                            className="group relative border-2 border-dashed border-[#D2D2D7] rounded-[20px] p-12 transition-all hover:border-[#0071E3] hover:bg-[#F5F5F7] cursor-pointer text-center"
                        >
                            <input type="file" ref={fileInputRef} onChange={handleFile} className="hidden" accept=".xlsx,.xls" />
                            <div className="space-y-4">
                                <div className="w-16 h-16 bg-[#F5F5F7] rounded-full flex items-center justify-center mx-auto group-hover:bg-white transition-colors">
                                    <svg className="w-8 h-8 text-[#0071E3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                                    </svg>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-lg font-medium">Arrastra tu Excel aquí</p>
                                    <p className="text-[#86868B]">o selecciona un archivo desde tu equipo</p>
                                </div>
                            </div>
                        </div>

                        {file && (
                            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="space-y-10">
                                <div className="flex items-center justify-between bg-[#F5F5F7] rounded-xl px-5 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="text-[#34C759]">
                                            <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                            </svg>
                                        </div>
                                        <span className="font-medium truncate max-w-[300px]">{file.name}</span>
                                    </div>
                                    <button onClick={() => setFile(null)} className="text-[#86868B] hover:text-[#FF3B30] transition-colors">
                                        <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                        </svg>
                                    </button>
                                </div>

                                <div className="space-y-6">
                                    <div className="pt-6 border-t border-[#F2F2F7]">
                                        <h3 className="text-sm font-semibold text-[#86868B] uppercase tracking-wider mb-4">Resumen del archivo</h3>
                                        <div className="flex items-center justify-between bg-white border border-[#F2F2F7] rounded-xl px-5 py-4">
                                            <span className="text-lg font-medium">Filas detectadas</span>
                                            <span className="text-2xl font-semibold text-[#0071E3]">{rowCount}</span>
                                        </div>
                                    </div>

                                    <div className="space-y-3">
                                        <label className="block text-sm font-semibold text-[#86868B] uppercase tracking-wider">Mes de las Planillas</label>
                                        <select 
                                            value={mes} 
                                            onChange={(e) => setMes(e.target.value)}
                                            className="w-full bg-[#F5F5F7] border-none rounded-xl px-5 py-4 font-medium focus:ring-2 focus:ring-[#0071E3] transition-all outline-none appearance-none"
                                        >
                                            {['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'].map(m => (
                                                <option key={m} value={m}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <button 
                                        onClick={() => setShowAlert(true)}
                                        className="w-full bg-[#0071E3] text-white text-lg font-semibold py-4 rounded-xl shadow-[0_4px_14px_rgba(0,113,227,0.3)] hover:bg-[#0077ED] hover:shadow-[0_6px_20px_rgba(0,113,227,0.4)] hover:-translate-y-0.5 transition-all active:scale-[0.98]"
                                    >
                                        Procesar archivo
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </motion.div>
                )}

                {(status === 'processing' || status === 'success' || status === 'failed') && (
                    <motion.div
                        key="modal"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 flex items-center justify-center px-6"
                    >
                        <div className="absolute inset-0 bg-white/60 backdrop-blur-xl"></div>
                        
                        <AnimatePresence mode="wait">
                            {status === 'processing' && (
                                <motion.div
                                    key="processing-content"
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    exit={{ scale: 1.05, opacity: 0 }}
                                    transition={{ duration: 0.3 }}
                                    className="bg-white rounded-[32px] shadow-[0_20px_60px_rgba(0,0,0,0.1)] border border-[#F2F2F7] p-12 max-w-[400px] w-full text-center relative z-10"
                                >
                                    <div className="mb-8">
                                        <div className="w-16 h-16 border-4 border-[#F2F2F7] border-t-[#0071E3] rounded-full animate-spin mx-auto"></div>
                                    </div>
                                    <h2 className="text-2xl font-semibold mb-2">Procesando archivos…</h2>
                                    <p className="text-[#86868B]">Esto puede tardar unos segundos</p>
                                    
                                    <div className="mt-8 space-y-3">
                                        <div className="w-full bg-[#F5F5F7] rounded-full h-2 overflow-hidden">
                                            <motion.div 
                                                className="bg-[#0071E3] h-full"
                                                animate={{ width: `${progress.percent}%` }}
                                                transition={{ duration: 0.5 }}
                                            />
                                        </div>
                                        <div className="flex justify-between text-xs font-semibold text-[#86868B]">
                                            <span>{progress.percent}%</span>
                                            <span className="truncate max-w-[150px]">{progress.lastItem || 'Iniciando...'}</span>
                                        </div>
                                    </div>
                                </motion.div>
                            )}

                            {status === 'success' && (
                                <motion.div
                                    key="success-content"
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                                    className="bg-white rounded-[32px] shadow-[0_20px_60px_rgba(0,0,0,0.1)] border border-[#F2F2F7] p-12 max-w-[480px] w-full text-center relative z-10"
                                >
                                    <div className="w-20 h-20 bg-[#34C759] rounded-full flex items-center justify-center mx-auto mb-8 shadow-[0_8px_20px_rgba(52,199,89,0.3)] text-white text-4xl">
                                        ✓
                                    </div>
                                    <h2 className="text-3xl font-semibold mb-10">Proceso completado</h2>
                                    
                                    <div className="grid grid-cols-2 gap-4 mb-8">
                                        {[
                                            { label: 'Generados', val: results?.total, color: 'text-[#1D1D1F]' },
                                            { label: 'PDFs', val: results?.result?.exitos, color: 'text-[#1D1D1F]' },
                                            { label: 'OSDE', val: results?.processed_items?.filter((i:any) => i.status === 'success' && i.category === 'OSDE').length, color: 'text-[#0071E3]' },
                                            { label: 'No OSDE', val: results?.processed_items?.filter((i:any) => i.status === 'success' && i.category === 'NO OSDE').length, color: 'text-[#1D1D1F]' }
                                        ].map((stat, idx) => (
                                            <div key={idx} className="bg-[#F5F5F7] rounded-2xl p-5 text-left">
                                                <p className="text-xs font-bold text-[#86868B] uppercase tracking-wider mb-1">{stat.label}</p>
                                                <p className={`text-2xl font-semibold ${stat.color}`}>{stat.val || 0}</p>
                                            </div>
                                        ))}
                                    </div>

                                    {results?.processed_items?.filter((i: any) => i.status === 'error').length > 0 && (
                                        <div className="mb-10 text-left">
                                            <h3 className="text-sm font-semibold text-[#86868B] uppercase tracking-wider mb-4 px-1">Errores detectados</h3>
                                            <div className="space-y-2 max-h-[160px] overflow-y-auto pr-2 custom-scrollbar">
                                                {results.processed_items
                                                    .filter((i: any) => i.status === 'error')
                                                    .map((item: any, idx: number) => (
                                                        <div key={idx} className="bg-[#FFF2F2] border border-[#FFD6D6] rounded-xl p-4 flex items-start gap-3">
                                                            <div className="mt-0.5 text-[#FF3B30]">
                                                                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                                                </svg>
                                                            </div>
                                                            <div>
                                                                <p className="text-sm font-semibold text-[#1D1D1F]">{item.name}</p>
                                                                <p className="text-xs text-[#FF3B30] mt-0.5">{item.error_msg}</p>
                                                            </div>
                                                        </div>
                                                    ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="space-y-4">
                                        <a href={`${API_BASE_URL}${results?.zip_url}`} className="block w-full bg-[#0071E3] text-white text-lg font-semibold py-4 rounded-xl shadow-[0_4px_14px_rgba(0,113,227,0.3)] hover:bg-[#0077ED] hover:shadow-[0_6px_20px_rgba(0,113,227,0.4)] hover:-translate-y-0.5 transition-all active:scale-[0.98]">
                                            Descargar ZIP
                                        </a>
                                        <button onClick={() => window.location.reload()} className="text-[#0071E3] font-medium hover:underline">
                                            Procesar otro archivo
                                        </button>
                                    </div>
                                </motion.div>
                            )}

                            {status === 'failed' && (
                                <motion.div
                                    key="failed-content"
                                    initial={{ scale: 0.9, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ type: 'spring', damping: 25, stiffness: 300 }}
                                    className="bg-white rounded-[32px] shadow-[0_20px_60px_rgba(0,0,0,0.1)] border border-[#F2F2F7] p-12 max-w-[400px] w-full text-center relative z-10"
                                >
                                    <div className="w-20 h-20 bg-[#FF3B30] rounded-full flex items-center justify-center mx-auto mb-8 shadow-[0_8px_20px_rgba(255,59,48,0.3)] text-white text-4xl">
                                        !
                                    </div>
                                    <h2 className="text-2xl font-semibold mb-2">Algo salió mal</h2>
                                    <p className="text-[#86868B] mb-8">{error || 'Ha ocurrido un error inesperado'}</p>
                                    
                                    <button onClick={() => setStatus('upload')} className="w-full bg-[#1D1D1F] text-white text-lg font-semibold py-4 rounded-xl transition-all hover:bg-black active:scale-[0.98]">
                                        Reintentar
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DriveProcessor;
