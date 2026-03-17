import React, { useState, useEffect } from 'react';
import { Menu, Bell } from 'lucide-react';

const Header = ({ onMenuToggle }) => {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => setTime(new Date()), 60000);
        return () => clearInterval(interval);
    }, []);

    const formattedDate = time.toLocaleDateString('es-AR', {
        weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
    });
    const formattedTime = time.toLocaleTimeString('es-AR', {
        hour: '2-digit', minute: '2-digit',
    });

    return (
        <header className="sticky top-0 z-30 bg-white border-b border-border-light">
            <div className="flex items-center justify-between px-4 md:px-6 lg:px-8 h-14">
                <div className="flex items-center gap-4">
                    <button
                        onClick={onMenuToggle}
                        className="lg:hidden p-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
                    >
                        <Menu size={18} />
                    </button>

                    <span className="hidden md:block text-xs text-text-tertiary capitalize">
                        {formattedDate} — {formattedTime}
                    </span>
                </div>

                <div className="flex items-center gap-3">
                    <span className="text-[10px] font-medium text-status-green border border-green-200 bg-green-50 px-2.5 py-1 rounded">
                        ● Datos de simulación -prueba beta-
                    </span>

                    <button className="relative p-1.5 rounded text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors">
                        <Bell size={16} />
                        <span className="absolute top-0.5 right-0.5 w-1.5 h-1.5 rounded-full bg-status-red" />
                    </button>

                    <div className="w-7 h-7 rounded bg-navy-800 flex items-center justify-center text-white text-[10px] font-bold">
                        CL
                    </div>
                </div>
            </div>
        </header>
    );
};

export default Header;
