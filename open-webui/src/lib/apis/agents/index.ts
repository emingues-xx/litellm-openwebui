import { OPENAI_API_BASE_URL } from '$lib/constants';

const AGENTS_API_BASE_URL = `${OPENAI_API_BASE_URL}/api`;

export const getAgents = async (token: string, userEmail: string) => {
    let error = null;

    const res = await fetch(`${AGENTS_API_BASE_URL}/agents`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'authorization': `Bearer ${token}`,
            'X-OpenWebUI-User-Email': userEmail
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .catch((err) => {
            console.log(err);
            if ('detail' in err) {
                error = err.detail;
            } else {
                error = 'Server connection failed';
            }
            return null;
        });

    if (error) {
        throw error;
    }

    return res.agents || [];
};

export const getAgentById = async (token: string, userEmail: string, id: string) => {
    let error = null;

    const res = await fetch(`${AGENTS_API_BASE_URL}/agents/${id}`, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'authorization': `Bearer ${token}`,
            'X-OpenWebUI-User-Email': userEmail
        }
    })
        .then(async (res) => {
            if (!res.ok) throw await res.json();
            return res.json();
        })
        .catch((err) => {
            console.log(err);
            if ('detail' in err) {
                error = err.detail;
            } else {
                error = 'Server connection failed';
            }
            return null;
        });

    if (error) {
        throw error;
    }

    return res.agent || null;
};
